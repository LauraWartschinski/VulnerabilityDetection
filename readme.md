# VUDENC - Vulnerability Detection with Deep Learning on a Natural Codebase

This is VUDENC, a project and master thesis for learning security vulnerability features from a large natural code basis using deep learning. The goal is to scrape a lot of security related commits of Python code from Github, process them and train a deep neural network on classifying code tokens and their context into 'vulnerable' and 'not vulnerable'. Word2Vec is used as embedding, and Long Short Term Memory networks for feature extraction.

## Background


![Architecture of the model](https://github.com/LauraWartschinski/VulnerabilityDetection/blob/master/img/Architecture.png)


For an exhaustive description of the theoretical background of this work, refer to the thesis itself, available as a pdf and tex file in the Master Thesis folder. A brief summary:
Vulnerability detection is crucial in preventing dangerous software exploits. There are several approaches including static and dynamic analysis, but recently, machine learning has been applied in various ways to create better models and tools. Because many tools rely on human experts to define features that make up vulnerabilities, they are subjective and require a lot of time-consuming manual work. Therefore, it is desireable to automatically learn vulnerability features with machine learning algorithms that can later recognize those typical patterns of vulnerable code and warn the user.

There are many possible ways of representing source code and embedding it in a suitable format, in varying granularity (from the file level down to the code itself). This approach works directly on the code itself and attempts classification on the level of individual code tokens, so it can highlight where exactly a vulnerability might be located in the code.

The data for this work is mined from Github. If a code snippet was changed in a commit that has a message like "fix sql injection issue", it is assumed that the part of the code that was changed was vulnerable before, and everything else is not vulnerable or at least of unclear status. The labels are thus generated purely from the commit context. The code tokens (in text form, such as "if" or "+" or "return" or "x") are embedded in a numerical vector format using a word2vec model that was trained on a large Python corpus before. 

![Architecture of the model](https://github.com/LauraWartschinski/VulnerabilityDetection/blob/master/img/exampleXSSsidebyside.png)

To learn the features, an LSTM (long short term memory) network is used. LSTMs are similar to standard RNNs - they have a internal state, a 'memory', that allows them to model sequential data and take the context of the current input into account - but they are better suited for long term dependencies as they don't suffer from the problem of vanishing and exploding gradients. A single code token can not be vulnerable or safe (what about "if"? what about "return"?), but it's effect only becomes apparent when put into context with the tokens that came before it. This is why an LSTM that uses its memory to model the data is useful to learn the correct features.


![Focus area and context](https://github.com/LauraWartschinski/VulnerabilityDetection/blob/master/img/FocusBlocks.png)

In a given source file, small focus areas (blue) of length n are classified by taking the source code around them (their context of length m) and using this moving window of attention to create samples. Each sample is labeled depending on whether it contains code that is vulnerable (i.e. that was changed in a security-related commit).In the image, A and D are contexts that are not labeled vulnerable, while B and C are labeled as vulnerable because they (partly) contain vulnerable code, depicted in red. The tokens making up that sample are embedded using word2vec and the LSTM is trained on those samples. 


In the same way, a new piece of sourcecode can be analyzed, taking the context of each token to classify it as vulnerable or not.

## Code


### 1. Training the Word2Vec model

The word2vec model is trained on a large set of python code which is simply concatenated. 
If you just want to use the word2vec model, simply use the trained model (w2v/word2vec_withString10-100-200.model), or extract the prepared corpus (pythontraining_edit.txt) and train it yourself using w2v_trainmodel.py (step 1.5). The datasets and corpus can also be found [on zenodo.org](https://zenodo.org/record/3559480#.XeTMzdVG2Hs). Otherwise, all steps from the beginning are outlined below.

Step 1.1: To create the corpus, enough python code has to be downloaded. The Repository Mining from [pydriller](https://pydriller.readthedocs.io/) is used to accomplish this task. The results are saved in the file pythontraining.txt.

```
python3 w2v_pythoncorpus.py
```

Step 1.2: Since there are syntax and indentation errors in those files, the following script fixes those. Note that with changes over time, different syntax errors might be introduced if the code is re-downloaded, which means that the script would need to be changed to fix those. The results are saved in pythontraining_edit.txt.

```
python3 w2v_cleancorpus.py
```

Step 1.3: Next, the python tokenizer is applied to retrieve the python source code tokens. The tokenizer can be set to handle strings differently by giving the parameter "withString" or "without String". Without string would indicate that all strings are replaced by a generic string token, while the other option (with string) leaves them as they are.

```
python3 w2v_tokenize.py withString
```

Step 1.4: The results of the previous step are saved as a bunch of files of the form 'pythontraining_withString_39.py' etc. This is because to save a lot of large files often is relatively slow, and handling them in batches is a significant improvement. The outputs are merged into a single file with the following script, which creates the file pythontraining_withString_X.py or pythontraining_withoutString_X.py, respectively. Those can also be found in the repository and in the zenodo dataset.

```
python3 w2v_mergecorpus.py
```


1.5: Finally, the word2vec model can be trained.

```
python3 w2v_trainmodel.py withString
```

This trains a word2vec model on the code and saves it. The mode can be set via a parameter to be either "withString" or "withoutString" and take the tokenized data that corresponds to that setting as a basis for training. The hyperparameters, such as vector dimensionality, number of iterations, and minimum amount of times a token has to be appear, can be set in the file.

It can be tried out like this just to play around with it a little:

```

>>> from gensim.models import Word2Vec, KeyedVectors
>>> model = Word2Vec.load("w2v/word2vec_withString10-100-200.model")
>>> model.wv.most_similar("if")
[('elif', 0.823542594909668), ('assert', 0.6754689812660217), ('and', 0.5552898645401001), ('assert_', 0.5546900033950806), ('or', 0.5151466131210327), ('continue', 0.445793479681015), ('asserttrue', 0.4425083100795746), ('while', 0.4388786852359772), ('return', 0.4170145094394684), ('assert_true', 0.41424062848091125)]
>>> model.wv.most_similar("count")
[('len', 0.512725293636322), ('num', 0.47855937480926514), ('total', 0.4754355847835541), ('max', 0.4658457636833191), ('depth', 0.4396299421787262), ('num_elements', 0.43482276797294617), ('length', 0.42664003372192383), ('size', 0.4246782660484314), ('cnt', 0.4217599332332611), ('position', 0.4216340184211731)]
>>> model.wv.most_similar("split")
[('lstrip', 0.6412516236305237), ('rstrip', 0.6404553055763245), ('rsplit', 0.61777263879776), ('strip', 0.6153339743614197), ('endswith', 0.5643146634101868), ('rfind', 0.5499937534332275), ('replace', 0.5499789714813232), ('rindex', 0.5488905310630798), ('startswith', 0.5430475473403931), ('splitlines', 0.5389511585235596)]
>>> model.wv.most_similar("x")
[('y', 0.7471214532852173), ('z', 0.5951355695724487), ('v', 0.5195837020874023), ('n', 0.4870358109474182), ('t', 0.47216174006462097), ('b', 0.4698690176010132), (')', 0.46523964405059814), ('p', 0.46154212951660156), ('2', 0.4609290063381195), ('k', 0.45710060000419617)]
>>> model.wv.most_similar("+")
[('+=', 0.6324988007545471), ('/', 0.581507682800293), ('*', 0.5298827290534973), ('&', 0.4750611186027527), ('<', 0.47204822301864624), ('split', 0.47001397609710693), (';', 0.45467206835746765), ('%', 0.44483357667922974), ('?', 0.4437963664531708), ('-', 0.4356187582015991)]
```


### 2. Creating the data and training the LSTM model

To recreate the datasets for vulnerabilities, download the full dataset with diffs from [zenodo.org](https://zenodo.org/record/3559203#.XeRoytVG2Hs) and continue with step 2.4, or the vulnerability datasets and continue in step 2.5 to train the LSTM models, or download the trained models and continue in step 2.6 to try them out.

Otherwise, all steps are listed below.

Step 2.1: First, it is neccessary (or at least highly recommended) to get a github API access token. Create it here: https://github.com/settings/tokens. Save the token in a file called 'access' in the same folder as the python scripts. To download a lot of commits, the following script is used: By modifying it, the keywords that are used to fetch the commits can be altered. The results are saved in 'all_commits.json'.

```
python3 scrapingGithub.py
```

Step 2.2: Repositories that are just there to demonstrate a vulnerability, to set up a capture-the-flag-type of challenge, or carry out an attack are not desireable for the dataset. The repository name and the content of the readme.md file are checked with the following script to filter out some of those already. The results are saved in DataFilter.json, which keeps track of the 'flags' set for each repository.

```
python3 filterShowcases.py
```

Step 2.3: Next, the commits are checked to see if they contain python code, and to download the diff files. While this is done, the file 'DataFilter.json' is saved to store information about which repositories and commits contain python and which don't (in addition to the info about showcases). The resulting data with the commits itself is stored in the file PyCommitsWithDiffs.json.

```
python3 getDiffs.py
```

Step 2.4: After creating the whole dataset with diffs, or downloading it from [zenodo.org](https://zenodo.org/record/3559203/export/hx#.XeTOTNVG2Hs), the dataset for each vulnerability can be created. This python script takes one argument which specifies which subset of data should be used to prepare the dataset (in the example, everything relevant to sql injections.)  This script does a lot of the main work. It reads the file 'PyCommitsWithDiffs.json', checks a lot of contraints and downloads the full source code of the changed files. It also identifies changed parts and comments and collects all relevant information in a file. The result is saved in the file 'data/plain_sql', 'data/plain_brute_force' etc. They are also available on [zenodo.org](https://zenodo.org/record/3559841#.XeVaZNVG2Hs).

```
python3 getData.py sql
```

Step 2.5: Next, the data has to be split at random in three segments: training, validating and final testing. This script takes one argument, the vulnerability / data subset it should work on which was created in the previous step. The data is shuffled randomly and then split in parts of 70%, 15% and 15% (training, validation and final test set), and the tokens are encoded using the loaded word2vec model (that should be created according to the previous steps!). Then, the LSTM model is trained and saved as model/LSTM_model_sql.h5 and so forth.


```
python3 makemodel.py sql
```


Step 2.6:  Any model can be tried out on the final test set (which it has not been trained on) by using the script trymodel. It loads the model and the final test set, prints some statistics, and calculates precision, accuracy, recall and F1 score for the model. The only paramter is the type of vulnerability.


```
python3 trymodel.py remote_code_execution
14412 samples in the final test set.
percentage of vulnerable samples: 9.04%
absolute amount of vulnerable samples in test set: 1303
Accuracy: 0.9811268387454899
Precision: 0.9598572702943801
Recall: 0.8257866462010744
F1 score: 0.887789
```

The model can also be applied to code to make predictions. Some code has been downloaded for demonstration purposes. Go to [Examples](https://github.com/LauraWartschinski/VulnerabilityDetection/blob/master/examples.md) for further instructions.