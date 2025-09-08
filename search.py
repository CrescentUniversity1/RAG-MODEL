import torch
from sentence_transformers.util import cos_sim
from utils.embedding import load_model

def find_response(user_query, dataset, embeddings, model=None, threshold=0.6):
    """
    Find the best matching answer to the user_query using cosine similarity.
    Returns: response (str), department (str or None), score (float), related_questions (list of str)
    """

    # Load model if not provided
    if model is None:
        model = load_model()

    # Encode query
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    cosine_scores = cos_sim(query_embedding, embeddings)[0]

    # Get best match
    best_score = torch.max(cosine_scores).item()
    best_idx = torch.argmax(cosine_scores).item()

    # If below threshold, return fallback
    if best_score < threshold:
        return "😕 I’m not sure how to answer that.", None, best_score, []

    # Retrieve best matching row
    best_row = dataset.iloc[best_idx]
    response = best_row["answer"]
    department = best_row.get("department", None)

    # Get top 4 related (excluding top one)
    top_k = torch.topk(cosine_scores, k=4)
    top_related = []
    for idx in top_k.indices.tolist():
        if idx != best_idx:
            question = dataset.iloc[idx]["question"]
            if question not in top_related:
                top_related.append(question)

    return response, department, best_score, top_related
