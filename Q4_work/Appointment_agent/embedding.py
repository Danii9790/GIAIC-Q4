import pandas as pd
from agents import OpenAIChatCompletionsModel, AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec
import os
import glob
from dotenv import load_dotenv
import json
import openai

load_dotenv()

# Gemini API key - use synchronous client for embeddings
external_client = openai.OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=external_client)

# Pinecone API key
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

def prepare_text_from_row(row, filename):
    """Convert a DataFrame row to descriptive text"""
    text_parts = []

    # Add file context
    text_parts.append(f"Source: {filename}")

    # Add disease information if present
    if 'Disease' in row:
        text_parts.append(f"Disease: {row['Disease']}")

    # Add specific information based on file type
    if 'medications' in filename.lower():
        if 'Medication' in row:
            text_parts.append(f"Medications: {row['Medication']}")
        elif 'Drug' in row:
            text_parts.append(f"Drug: {row['Drug']}")

    elif 'symptoms' in filename.lower():
        symptoms = [row[col] for col in row.index if 'Symptom' in col and pd.notna(row[col]) and row[col].strip() != '']
        if symptoms:
            text_parts.append(f"Symptoms: {', '.join(symptoms)}")

    elif 'diets' in filename.lower():
        if 'Diet' in row:
            text_parts.append(f"Diet Recommendation: {row['Diet']}")

    elif 'precautions' in filename.lower():
        precautions = [row[col] for col in row.index if 'Precaution' in col and pd.notna(row[col]) and row[col].strip() != '']
        if precautions:
            text_parts.append(f"Precautions: {', '.join(precautions)}")

    elif 'doctors' in filename.lower():
        # Handle doctors data
        for col in row.index:
            if pd.notna(row[col]) and str(row[col]).strip() != '' and col not in ['Unnamed: 0']:
                text_parts.append(f"{col}: {row[col]}")

    elif 'workout' in filename.lower():
        if 'Workout' in row:
            text_parts.append(f"Workout: {row['Workout']}")
        elif 'Exercise' in row:
            text_parts.append(f"Exercise: {row['Exercise']}")

    elif 'severity' in filename.lower():
        for col in row.index:
            if pd.notna(row[col]) and str(row[col]).strip() != '' and col not in ['Unnamed: 0']:
                text_parts.append(f"{col}: {row[col]}")

    elif 'description' in filename.lower() or 'Training' in filename:
        for col in row.index:
            if pd.notna(row[col]) and str(row[col]).strip() != '' and col not in ['Unnamed: 0']:
                text_parts.append(f"{col}: {row[col]}")

    return " | ".join(text_parts)

def process_csv_files():
    """Process all CSV files in the datasets folder"""
    dataset_files = glob.glob("datasets/*.csv")
    all_texts = []
    all_metadata = []

    print(f"Found {len(dataset_files)} CSV files to process...")

    for file_path in dataset_files:
        filename = os.path.basename(file_path)
        print(f"Processing {filename}...")

        try:
            df = pd.read_csv(file_path)

            # Remove unnamed columns
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            for idx, row in df.iterrows():
                text = prepare_text_from_row(row, filename)
                if text and len(text.strip()) > 0:
                    metadata = {
                        "source_file": filename,
                        "row_index": idx,
                        "text": text,
                        "filename": filename
                    }

                    # Add disease if available
                    if 'Disease' in row and pd.notna(row['Disease']):
                        metadata["disease"] = row['Disease']

                    all_texts.append(text)
                    all_metadata.append(metadata)

            print(f"[OK] Processed {len(df)} rows from {filename}")

        except Exception as e:
            print(f"[ERROR] Error processing {filename}: {e}")
            continue

    return all_texts, all_metadata

def create_pinecone_index(index_name):
    """Create Pinecone index if it doesn't exist"""
    if index_name not in [index.name for index in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=768,  # text-embedding-004 ka dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"[OK] Created new index: {index_name}")
    else:
        print(f"[INFO] Index {index_name} already exists")

    return pc.Index(index_name)

def batch_upload_embeddings(texts, metadata, index_name, batch_size=50):
    """Upload embeddings in batches to avoid rate limits"""
    index = create_pinecone_index(index_name)
    total_texts = len(texts)

    for i in range(0, total_texts, batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_metadata = metadata[i:i+batch_size]

        # Create embeddings for batch
        try:
            response = external_client.embeddings.create(
                model="text-embedding-004",
                input=batch_texts
            )

            vectors = []
            for j, (text, meta, embedding) in enumerate(zip(batch_texts, batch_metadata, response.data)):
                vector_id = f"{meta['source_file'].replace('.csv', '')}_{i + j}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding.embedding,
                    "metadata": meta
                })

            # Upsert to Pinecone
            index.upsert(vectors=vectors)
            print(f"[OK] Uploaded batch {i//batch_size + 1}/{(total_texts-1)//batch_size + 1} ({len(vectors)} embeddings)")

        except Exception as e:
            print(f"[ERROR] Error in batch {i//batch_size + 1}: {e}")
            continue

def main():
    """Main function to process all CSV files and upload embeddings"""
    print("Starting CSV file processing and embedding...")

    # Process all CSV files
    texts, metadata = process_csv_files()

    print(f"[INFO] Total texts prepared: {len(texts)}")

    if len(texts) == 0:
        print("[ERROR] No valid texts found to embed!")
        return

    # Upload embeddings to Pinecone
    index_name = "healthcare-embeddings"
    batch_upload_embeddings(texts, metadata, index_name)

    print(f"[OK] Successfully uploaded {len(texts)} embeddings to Pinecone!")

    # Test with a sample query
    test_query(index_name)

def test_query(index_name):
    """Test the index with a sample query"""
    print("\n[INFO] Testing with sample queries...")

    index = pc.Index(index_name)

    test_queries = [
        "fever medicine",
        "diabetes symptoms",
        "allergy treatment",
        "heart disease precautions"
    ]

    for query in test_queries:
        print(f"\n[QUERY] {query}")

        try:
            query_emb = external_client.embeddings.create(
                model="text-embedding-004",
                input=query
            ).data[0].embedding

            result = index.query(
                vector=query_emb,
                top_k=3,
                include_metadata=True
            )

            print("[RESULTS]")
            for i, match in enumerate(result["matches"], 1):
                print(f"{i}. Score: {match['score']:.4f}")
                print(f"   Source: {match['metadata'].get('source_file', 'Unknown')}")
                print(f"   Text: {match['metadata']['text'][:150]}...")

        except Exception as e:
            print(f"[ERROR] Error with query '{query}': {e}")

if __name__ == "__main__":
    main()

