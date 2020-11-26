# Introduction

# Engines

In this section, the different engines are descibred.

- Language supported
- APIs
- Big Data strategies
- Type of scheduling (mostly if ray is included)
- Limitations

## Apache Spark

## Dask

## Ray (if time allows)

## Comparison

Table and/or short summary on the different engines.

# File Systems

## NFS

- Rationale for using NFS; for ease of use / quick deployment.
- Limitation of NFS.
- 1-2 Sentences on pNFS.

## Lustre

- Rationale for using Lustre; parrallel for better speed .
- Limitation of Lustre
- Why we choose Lustre over pNFS; better adoption in HPCs.

# Methods

## Infrastructure

Description of slashbin cluster.

## Dataset

- Big Brain
- CoRR
- BOLD 500 (if time allows for additional applications)

## Incrementation

<!-- Should we save to data to disk between each iteration? -->

- 1s vector

## Incrementation v2.0

- Increment with next vector instead of 1s vector.
- Increase inter-worker communication.
- Could vary how much communication is done by varying an alpha probability of taking next vs 1s vector.

## Histogram

<!-- Only include the NumPy version. -->

## BIDS App Example

- Engines mostly used for quick distribution/parrallism. Should not diverge in performance.

## K-Means

- Lazy random sampling of Dask bag is now available. [see](https://github.com/dask/dask/pull/6208)
- Provides a more complex application.

## Additional

- Table containing the data size processed for each experiments. (Maybe in Results?)

## Others (if time allows)

# Results

# Discussion

# Conclusion
