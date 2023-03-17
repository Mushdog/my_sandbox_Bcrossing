# my_sandbox_Bcrossing
Code for Book-crossing dataset.

# This is a short description of my code. For some reason, it is not a github specification. I'm sorry this is the first time I've written a readme file and some of the terminology aspects may not be expressed.

I think we can start by looking at the readme file of nickmvincent/surprise_sandbox https://github.com/nickmvincent/surprise_sandbox.

I added the preprocessed Book-Crossing dataset based on their code. It should be noted in advance that in order to save AWS EC2 storage costs, I ran separate code with Movielen-1M and Book-Crossing data, i.e., two datasets correspond to two copies of the code. I made only minimal code changes to adapt to the Book-Crossing dataset, which is not fine, mature, or professional. This is a good reflection of my current level.

# A. Cloud Compute and Environment Configuration:
Since the k-NN and FunkSVD algorithms used in the recommended system involve large matrix operations, they require sufficient RAM. reminded by the nickmvincent’s code, I used the AWS EC2 Instance service. Some algorithms require, for example, m5.8xlarge configurations with 32 vGPUs and 128 GiB Memory. The rest of the calculations can be switched back to the normal m5.large configuration. Of course, the setup of jupyter notebook on the virtual machine involves some more detailed and routine operations.
Please follow the readme file of nickmvincent/surprise_sandbox for environment configuration:
Be sure to load the Suprise fork customized by nickmvincent.

# B. Input for the processed dataset:
The pre-processed Book-Crossing dataset is generated in the fellowshipai > Book-Crossing-preprocess.ipynb. In order to embed and match the code afterwards, a file named bcrossing.zip containing the files users.csv, ratings.csv, books.csv needs to be generated manually and then made into an http link. This link is used in the Surprise > surprise > builtin_datasets.py module. There are also some modifications to the sandbox.py load module to fit the dataset.
I made the link using the AWS S3 service, which is currently under the Free tier free
service period, so I have not closed the link for now.

# C. The order of running documents:
## The bash_scripts file lists the scripts to run.
1. sandbox.py to get
/logs
files.
2. process_all.py
to get all_results.csv
3. centroids-checkpoint.ipynb
to get some .json files
4. data_strikes_results.ipynb
to get the final analysis results
