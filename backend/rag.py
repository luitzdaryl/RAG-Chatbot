import ollama
import yaml

# Load config once at startup
with open('./config.yaml', 'r') as f:
    config = yaml.safe_load(f)

EMBEDDING_MODEL      = config['embedding_model']
LANGUAGE_MODEL       = config['language_model']
DATASET_PATH         = config['dataset_path']
TOP_K                = config['top_k']
SIMILARITY_THRESHOLD = config['similarity_threshold']
SYSTEM_PROMPT        = config['system_prompt']

VECTOR_DB = []


# ============================================================
# LOAD DATASET
# ============================================================

with open(DATASET_PATH, 'r', encoding='utf-8') as file:
    dataset = [line.strip() for line in file.readlines() if line.strip()]


# ============================================================
# EMBEDDINGS
# ============================================================

def generate_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response['embeddings'][0]


def add_chunk_to_database(chunk):
    embedding = generate_embedding(chunk)
    VECTOR_DB.append({
        'text': chunk,
        'embedding': embedding
    })


# Build vector database at startup
for chunk in dataset:
    add_chunk_to_database(chunk)


# ============================================================
# SIMILARITY
# ============================================================

def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot_product / (norm_a * norm_b)


def retrieve(query, top_k=TOP_K):
    query_embedding = generate_embedding(query)
    similarities = []

    for item in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, item['embedding'])
        if similarity >= SIMILARITY_THRESHOLD:
            similarities.append({
                'text': item['text'],
                'similarity': similarity
            })

    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]


# ============================================================
# ORIGINAL (non-streaming) CHAT FUNCTION — kept for reference
# ============================================================

def ask_ai(user_query):
    retrieved_knowledge = retrieve(user_query)

    context = '\n'.join([
        f"- {item['text']}"
        for item in retrieved_knowledge
    ])

    system_prompt = system_prompt = SYSTEM_PROMPT.format(context=context)

    response = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ]
    )

    return {
        "response": response['message']['content'],
        "sources": retrieved_knowledge
    }


# ============================================================
# STREAMING CHAT FUNCTION
# ============================================================

def ask_ai_stream(user_query, retrieved_knowledge=None):
    if retrieved_knowledge is None:
        retrieved_knowledge = retrieve(user_query)

    context = '\n'.join([
        f"- {item['text']}"
        for item in retrieved_knowledge
    ])

    system_prompt = f"""
You are a helpful AI assistant.

Answer the user's question using ONLY the retrieved context below.

If the answer cannot be found in the context, say:
"I could not find the answer in the provided knowledge base."

Retrieved Context:
{context}
"""

    response = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ],
        stream=True  # enables token-by-token streaming
    )

    for chunk in response:
        token = chunk['message']['content']
        if token:
            yield token