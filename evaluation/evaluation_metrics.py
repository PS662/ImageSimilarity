import os
import argparse
import requests
from tqdm import tqdm
from typing import List, Dict
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np
import random

API_URL = "http://localhost:8000/search_with_image"
HEADERS = {"accept": "application/json"}


def get_rank(results: List[dict], ground_truth: str) -> int:
    for idx, result in enumerate(results):
        if os.path.basename(result["image_uri"]) == ground_truth:
            return idx + 1  # Rank is 1-based
    return 0  # Return 0 if the ground truth is not found


def Precision(results: List[dict], ground_truth: str, k: int) -> float:
    relevant_items = sum(
        1 for result in results[:k] if os.path.basename(result["image_uri"]) == ground_truth
    )
    return relevant_items / k if k > 0 else 0.0


def Recall(results: List[dict], ground_truth: str, k: int) -> float:
    relevant_items = sum(
        1 for result in results[:k] if os.path.basename(result["image_uri"]) == ground_truth
    )
    total_relevant = 1  # Total relevant items in this setup (ground truth is a single item)
    return relevant_items / total_relevant if total_relevant > 0 else 0.0


def F1_Score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def DCG(scores: List[float], k: int) -> float:
    return sum(
        score / np.log2(idx + 2) for idx, score in enumerate(scores[:k])
    )


def NDCG(results: List[dict], ground_truth: str, k: int) -> float:
    # FIXME: Replace similarity scores with true relevance scores when available
    # Extract similarity scores directly for DCG calculation
    relevance_scores = [
        (1 - result["distance"]) if os.path.basename(result["image_uri"]) == ground_truth else 0
        for result in results
    ]
    
    ideal_scores = sorted(relevance_scores, reverse=True)
    
    dcg = DCG(relevance_scores, k)
    idcg = DCG(ideal_scores, k)
    
    return dcg / idcg if idcg > 0 else 0.0


def get_cdf(values):
    bin_edges = np.percentile(values, [0, 5, 10, 25, 50, 75, 90, 100])
    counts, bins_count = np.histogram(values, bins=bin_edges)
    pdf = counts / sum(counts)
    cdf = np.cumsum(pdf)
    return bins_count[1:], cdf


def get_rank_metrics(rank_list, rank_metrics_list):
    total_queries = len(rank_list)
    metrics = {}
    for rank in rank_metrics_list:
        rank_count = sum(r <= rank for r in rank_list)
        rank_percentage = rank_count / total_queries * 100
        metrics[rank] = rank_percentage
    return metrics


def plot_cdf(metric_values, metric_name, rank_metrics_list, quantiles_list, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    plt.figure(figsize=(15, 8))
    bins_count, cdf = get_cdf(metric_values)
    rank_metrics = get_rank_metrics(metric_values, rank_metrics_list)

    label = (
        f"{metric_name}: "
        f"Rank 1: {rank_metrics.get(1, 0):.2f}%, "
        f"Rank 5: {rank_metrics.get(5, 0):.2f}%, "
        f"Rank 10: {rank_metrics.get(10, 0):.2f}%, "
        f"Rank 100: {rank_metrics.get(100, 0):.2f}%\n"
    )

    # Plot percentiles
    for quantile in quantiles_list:
        quantile_val = np.percentile(metric_values, quantile)
        plt.scatter(
            quantile_val,
            quantile / 100,
            marker="x",
            color="black",
            s=200,
            label=f"{quantile}% < Rank {quantile_val:.2f}",
        )

    # Plot CDF
    plt.plot(bins_count, cdf, label=label, linewidth=2)
    plt.title(f"{metric_name} CDF", fontsize=20)
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xlabel("Rank", fontsize=15)
    plt.ylabel("Cumulative Percent of Queries", fontsize=15)

    # Configure axes
    major_locator = MultipleLocator(50)
    ax = plt.gca()
    ax.xaxis.set_major_locator(major_locator)
    ax.xaxis.set_major_formatter("{x:.0f}")
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))

    plt.legend(loc="lower right", fontsize=12)
    plt.ylim(bottom=0)
    plt.savefig(f"{cache_dir}/{metric_name}_cdf.png")
    plt.show()


def do_evaluation(test_folder, model_id, metrics_to_compute, k_values=None):
    image_files = [
        f for f in os.listdir(test_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
    ]
    ranks = []
    precision_values = []
    recall_values = []
    f1_values = []
    ndcg_values = []
    
    if k_values:
        top_k = max(k_values)
    else:
        top_k = len(image_files)
        
    for idx, image_file in enumerate(tqdm(image_files, desc=f"Evaluating model: {model_id}")):
        # FIXME: Quick hack to create a dummy ground truth
        # Ideally, we would have tags and we could use text embeddings to check similarity 
        # Here I am selecting random image uri for every odd index and for even assigning true
        ground_truth = image_file if idx % 2 == 0 else random.choice(
            [img for img in image_files if img != image_file]
        )
        file_path = os.path.join(test_folder, image_file)

        # Query Backend
        try:
            with open(file_path, "rb") as file:
                files = {"file": file}
                data = {"model_id": model_id, "top_k": top_k}
                response = requests.post(API_URL, files=files, data=data, headers=HEADERS)
                response.raise_for_status()
                task_id = response.json().get("task_id")
        except Exception as e:
            print(f"Error querying {image_file}: {e}")
            continue

        # Poll for Results
        poll_url = f"http://localhost:8000/poll_task_status/{task_id}"
        results = []
        try:
            poll_params = {"target_status": "SUCCESS", "timeout": 30, "retry_limit": 3}
            task_response = requests.get(poll_url, params=poll_params, headers=HEADERS).json()
            if task_response["status"] == "SUCCESS" and "result" in task_response:
                results = task_response["result"]
            elif task_response["status"] == "FAILURE":
                print(f"Task failed for {image_file}")
        except Exception as e:
            print(f"Error polling for task {task_id}: {e}")
            continue


        # Skip this image if no results
        if not results:
            print(f"No results for {image_file}. Skipping...")
            continue

        # Metrics
        rank = get_rank(results, ground_truth)
        if rank > 0:
            ranks.append(rank)

        if "Precision" in metrics_to_compute:
            precision_values.append(Precision(results, ground_truth, top_k))
        if "Recall" in metrics_to_compute:
            recall_values.append(Recall(results, ground_truth, top_k))
        if "F1-Score" in metrics_to_compute:
            precision = precision_values[-1] if precision_values else 0.0
            recall = recall_values[-1] if recall_values else 0.0
            f1_values.append(F1_Score(precision, recall))
        if "NDCG" in metrics_to_compute:
            ndcg_values.append(NDCG(results, ground_truth, top_k))

    return ranks, precision_values, recall_values, f1_values, ndcg_values


def get_dynamic_rank_metrics_list(max_k):
    rank_metrics_list = [1, 5, 10, 50, 100]
    if max_k > 100:
        rank_metrics_list.extend(range(200, max_k + 1, 100))
    return rank_metrics_list

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-folder-data", type=str, required=True)
    parser.add_argument("--model-id", type=str, required=True)
    parser.add_argument("--k-values", type=int, nargs="+", default=[10, 50, 100])
    parser.add_argument("--metrics", type=str, nargs="+", default=["MRR", "Precision", "Recall", "F1-Score", "NDCG"])
    parser.add_argument("--cache-dir", type=str, default=".")
    args = parser.parse_args()

    max_k = max(args.k_values)
    rank_metrics_list = get_dynamic_rank_metrics_list(max_k)
    quantiles_list = [25, 50, 75]

    ranks, precision_values, recall_values, f1_values, ndcg_values = do_evaluation(
        args.test_folder_data, args.model_id, args.metrics, args.k_values
    )
    
    print(f"Evaluation results: {ranks, precision_values, recall_values, f1_values, ndcg_values}")

    if "MRR" in args.metrics:
        plot_cdf(ranks, "MRR", rank_metrics_list, quantiles_list, args.cache_dir)
    if "NDCG" in args.metrics:
        plot_cdf(ndcg_values, "NDCG", rank_metrics_list, quantiles_list, args.cache_dir)
        
    #The ROC curve would be a better viz here
    #if "Precision" in args.metrics:
    #    plot_cdf(precision_values, "Precision", rank_metrics_list, quantiles_list, args.cache_dir)
    #if "Recall" in args.metrics:
    #    plot_cdf(recall_values, "Recall", rank_metrics_list, quantiles_list, args.cache_dir)
    #if "F1-Score" in args.metrics:
    #    plot_cdf(f1_values, "F1-Score", rank_metrics_list, quantiles_list, args.cache_dir)

if __name__ == "__main__":
    main()
