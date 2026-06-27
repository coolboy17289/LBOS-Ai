# Simple analysis script for LBOS-AI
# Computes basic statistics on a numeric vector

analyze_data <- function(data) {
  if (!is.numeric(data)) {
    stop("Input must be numeric")
  }

  n <- length(data)
  mean_val <- mean(data, na.rm = TRUE)
  sd_val <- sd(data, na.rm = TRUE)
  median_val <- median(data, na.rm = TRUE)
  min_val <- min(data, na.rm = TRUE)
  max_val <- max(data, na.rm = TRUE)

  cat("Summary Statistics:\n")
  cat("  Sample size:", n, "\n")
  cat("  Mean:", sprintf("%.4f", mean_val), "\n")
  cat("  Std Dev:", sprintf("%.4f", sd_val), "\n")
  cat("  Median:", sprintf("%.4f", median_val), "\n")
  cat("  Min:", sprintf("%.4f", min_val), "\n")
  cat("  Max:", sprintf("%.4f", max_val), "\n")

  invisible(list(n = n, mean = mean_val, sd = sd_val, median = median_val,
                 min = min_val, max = max_val))
}

# Example usage
if (!interactive()) {
  # When run as script, generate sample data and analyze
  set.seed(123)
  sample_data <- rnorm(100, mean = 50, sd = 10)
  analyze_data(sample_data)
}