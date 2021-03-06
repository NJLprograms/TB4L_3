from utils import read_ov, remove_punctuation
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import enum
from math import log10
import copy
from sklearn.metrics import recall_score, precision_score, f1_score, accuracy_score

tweet_id_index = 0
tweet_index = 1
label_index = 2

traceFV = open("trace_NB-BOW-FV.txt", "w")
evalFV = open("eval_NB-BOW-FV", "w")

class q1_classification(enum.Enum):
  YES = 'yes'
  NO = 'no'


class FV_MultinomialNB:
  def __init__(self):
    self.alpha = 0.01
    self.smoothing = 0.01
    self.number_of_good_tweets = 0
    self.number_of_bad_tweets = 0
    self.number_of_total_tweets = 0
    self.training_data = None
    self.good_words = dict()
    self.bad_words = dict()
    self.good_word_likelihoods = dict()
    self.bad_word_likelihoods = dict()
    self.vocab_length = 0
    return

  def fit(self, filename: str):
    ov = read_ov(filename)
    vectorizer = CountVectorizer(lowercase=True)
    rows = [row for row in ov.to_numpy()]

    self.training_data = rows

    tweet_ids = [row[tweet_id_index] for row in rows]
    tweets = [row[tweet_index].lower() for row in rows]
    q1_labels = [row[label_index] for row in rows]

    OV_tweets = vectorizer.fit_transform(tweets)

    # Set number of 'yes' and 'no' labels
    for label in q1_labels:
      if label == q1_classification.YES.value:
        self.number_of_good_tweets = self.number_of_good_tweets + 1
      else:
        self.number_of_bad_tweets = self.number_of_bad_tweets + 1
    #

    # define number of words in good dict and bad dict
    for document in self.training_data:
      for word in remove_punctuation(document[tweet_index].lower()).split():
        if document[label_index] == q1_classification.YES.value:
          if word in self.good_words:
            self.good_words[word] = self.good_words[word] + 1
          else:
            self.good_words[word] = 1
        else:
          if word in self.bad_words:
            self.bad_words[word] = self.bad_words[word] + 1
          else:
            self.bad_words[word] = 1
    
    # REMOVE ALL INSTANCES WITH ONLY ONE WORDS
    temp = copy.deepcopy(self.good_words)
    for word, word_count in temp.items():
      if word_count == 1:
        del self.good_words[word]

    temp = copy.deepcopy(self.bad_words)
    for word, word_count in temp.items():
      if word_count == 1:
        del self.bad_words[word]
      


    # set vocab length (merge both good and bad dicts and compute number of keys)
    self.vocab_length = len({**self.good_words, **self.bad_words}.keys())
    
    # define probabilities of words being in factual or non-factual claim
    for word, word_count in self.good_words.items():
      likelihood = float(word_count + self.smoothing) / (len(self.good_words) + self.smoothing * self.vocab_length)
      self.good_word_likelihoods[word] = likelihood

    for word, word_count in self.bad_words.items():
      likelihood = float(word_count + self.smoothing) / (len(self.bad_words) + self.smoothing * self.vocab_length)
      self.bad_word_likelihoods[word] = likelihood

    return

  def predict(self, filename):
    print
    results = []

    ov = read_ov(filename, header=None)
    vectorizer = CountVectorizer(lowercase=True)
    rows = [row for row in ov.to_numpy()]
    labels = []
    tpY = 0
    fpY = 0
    fnY = 0
    tpN = 0
    fpN = 0
    fnN = 0

    for row in rows:
      good_score = log10(self.number_of_good_tweets / self.vocab_length) + sum([log10(self.good_word_likelihoods.get(word, 1)) for word in row[tweet_index]])
      bad_score = log10(self.number_of_bad_tweets / self.vocab_length) + sum([log10(self.bad_word_likelihoods.get(word, 1)) for word in row[tweet_index]])
      good = good_score >= bad_score

      labels.append(row[label_index])

      tweetID = row[tweet_id_index]
      likelyClass = q1_classification.YES.value if good else q1_classification.NO.value
      likelyScore = good_score if good else bad_score
      correctClass = row[label_index]
      label = "correct" if correctClass == likelyClass else "wrong"
      
      if correctClass == q1_classification.YES.value:
        if likelyClass == q1_classification.YES.value and correctClass == q1_classification.YES.value:
          tpY += 1
        elif likelyClass == q1_classification.NO.value and correctClass == q1_classification.YES.value:
          fnY += 1
        elif likelyClass == q1_classification.YES.value and correctClass == q1_classification.NO.value:
          fpY += 1

      if correctClass == q1_classification.NO.value:
        if likelyClass == q1_classification.NO.value and correctClass == q1_classification.NO.value:
          tpN += 1
        elif likelyClass == q1_classification.YES.value and correctClass == q1_classification.NO.value:
          fnN += 1
        elif likelyClass == q1_classification.NO.value and correctClass == q1_classification.YES.value:
          fpN += 1


      results.append({"tweet_id": tweetID, "class": likelyClass, "score": good_score})
      traceFV.write(
          f'{tweetID}  {likelyClass}  {likelyScore}  {correctClass}  {label}\n')

    accuracy = accuracy_score(labels, [label["class"] for label in results])
    perClassPrecisionYes = tpY/(tpY + fpY)
    perClassPrecisionNo = 0

    if tpN != 0:
      perClassPrecisionNo = tpN/(tpN + fpN)

    perClassRecallYes = tpY/(tpY+fnY)
    perClassRecallNo = tpN/(tpN+fnN)

    perClassF1Yes = 2*(perClassRecallYes*perClassPrecisionYes) / (perClassRecallYes+perClassPrecisionYes)
    perClassF1No = 0

    if perClassRecallNo != 0:
      perClassF1No = 2*(perClassRecallNo*perClassPrecisionNo) / (perClassRecallNo+perClassPrecisionNo)

    traceFV.close()
    evalFV.write(f"{accuracy }\n{perClassPrecisionYes}  {perClassPrecisionNo}\n{perClassRecallYes}  {perClassRecallNo}\n{perClassF1Yes}  {perClassF1No}")
    evalFV.close()

    return results
