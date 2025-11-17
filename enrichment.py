#!/usr/bin/env python3
import argparse
import pandas as pd
from scipy.stats import fisher_exact
import statsmodels.stats.multitest as smm

def load_subset(file_path):
    """Load subset orthogroup IDs (one per line)."""
    return set(line.strip() for line in open(file_path) if line.strip())

def load_annotations(file_path):
    """
    Load annotation table in *long format*:
    orthogroup <TAB> term

    If an orthogroup has several terms → multiple lines.
    """
    df = pd.read_csv(file_path, sep="\t", header=None, names=["orthogroup", "term"])
    df = df.dropna()

    # Group terms per orthogroup
    grouped = df.groupby("orthogroup")["term"].apply(set).reset_index()
    grouped = grouped.rename(columns={"term": "terms"})
    return grouped

def build_contingency(df, subsetA, term):
    """Count a,b,c,d for one term."""
    a = sum((og in subsetA) and (term in terms) for og, terms in zip(df["orthogroup"], df["terms"]))
    b = sum((og in subsetA) and (term not in terms) for og, terms in zip(df["orthogroup"], df["terms"]))
    
    c = sum((og not in subsetA) and (term in terms) for og, terms in zip(df["orthogroup"], df["terms"]))
    d = sum((og not in subsetA) and (term not in terms) for og, terms in zip(df["orthogroup"], df["terms"]))
    
    return a, b, c, d

def main():
    parser = argparse.ArgumentParser(description="GO/COG enrichment using odds ratio (Fisher).")
    parser.add_argument("--subsetA", required=True, help="File with orthogroups of subset A (one per line).")
    parser.add_argument("--annotations", required=True,
                        help="TSV file *long format*: orthogroup <TAB> term")
    parser.add_argument("--out", required=True, help="Output TSV for enrichment results.")
    args = parser.parse_args()

    # Load data
    subsetA = load_subset(args.subsetA)
    ann = load_annotations(args.annotations)

    # Collect all unique terms
    all_terms = sorted({t for ts in ann["terms"] for t in ts})

    results = []
    for term in all_terms:
        a, b, c, d = build_contingency(ann, subsetA, term)

        if (a + b == 0) or (c + d == 0):
            continue

        OR, p = fisher_exact([[a, b], [c, d]])
        results.append([term, OR, p, a, b, c, d])

    df = pd.DataFrame(results,
        columns=["term", "odds_ratio", "p_value", "a", "b", "c", "d"]
    )

    # FDR
    df["FDR"] = smm.multipletests(df["p_value"], method="fdr_bh")[1]

    df = df.sort_values(["FDR", "odds_ratio"])

    df.to_csv(args.out, sep="\t", index=False)
    print(f"Done! Results written to: {args.out}")

if __name__ == "__main__":
    main()
