import requests
from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient
from msrest.authentication import CognitiveServicesCredentials
from pprint import pprint
import os
import re

sample_query_response = {
    "items": [
        {
            "tags": [
                "python",
                "iterator",
                "generator",
                "yield",
                "coroutine"
            ],
            "answers": [
                {
                    "owner": {
                        "user_id": 8458,
                        "display_name": "Douglas Mayle"
                    },
                    "score": 326,
                    "creation_date": 1224800643,
                    "answer_id": 231778,
                    "body": "<p><code>yield</code> is just like <code>return</code> - it returns whatever you tell it to (as a generator). The difference is that the next time you call the generator, execution starts from the last call to the <code>yield</code> statement. Unlike return, <strong>the stack frame is not cleaned up when a yield occurs, however control is transferred back to the caller, so its state will resume the next time the function is called.</strong></p>\n\n<p>In the case of your code, the function <code>get_child_candidates</code> is acting like an iterator so that when you extend your list, it adds one element at a time to the new list.</p>\n\n<p><code>list.extend</code> calls an iterator until it's exhausted. In the case of the code sample you posted, it would be much clearer to just return a tuple and append that to the list.</p>\n"
                },
                {
                    "owner": {
                        "user_id": 22656,
                        "display_name": "Jon Skeet"
                    },
                    "score": 188,
                    "creation_date": 1224800766,
                    "answer_id": 231788,
                    "body": "<p>It's returning a generator. I'm not particularly familiar with Python, but I believe it's the same kind of thing as <a href=\"http://csharpindepth.com/Articles/Chapter11/StreamingAndIterators.aspx\" rel=\"noreferrer\">C#'s iterator blocks</a> if you're familiar with those.</p>\n\n<p>The key idea is that the compiler/interpreter/whatever does some trickery so that as far as the caller is concerned, they can keep calling next() and it will keep returning values - <em>as if the generator method was paused</em>. Now obviously you can't really \"pause\" a method, so the compiler builds a state machine for you to remember where you currently are and what the local variables etc look like. This is much easier than writing an iterator yourself.</p>\n"
                }
            ],
            "owner": {
                "user_id": 18300,
                "display_name": "Alex. S."
            },
            "accepted_answer_id": 231855,
            "answer_count": 41,
            "score": 10146,
            "creation_date": 1224800471,
            "question_id": 231767,
            "title": "What does the &quot;yield&quot; keyword do?"
        }
    ]
}


class SentimentAnalyzer:
  def __init__(self):
        self.client = self.authenticateClient()

  # Creates client for sending requests to azure textanalytics api
  def authenticateClient(self):
    # TODO: Fill in the endpoint and key from Azure
    endpoint = ''
    key = ''

    credentials = CognitiveServicesCredentials(key)
    text_analytics_client = TextAnalyticsClient(endpoint=endpoint, credentials=credentials)
    return text_analytics_client

  # creates the 'documentsList' which will be sent to azure, for a set of answers.
  def createDocumentsList(self, answers):
      count = 1
      documentsList = []
      for answer in answers:
          count += 1
          document = self.createDocument(answer, count)
          documentsList.append(document)

      return documentsList

  # creates a document for one specific answer
  def createDocument(self, answer, count):
      body = self.removeMarkUps(answer["body"])
      # to get sentiment linked to answer_id use `str(answer["answer_id"])`` instead of str(count)`
      document = {
          "language": "en",
          "id": str(answer["answer_id"]),
          "text": body
      }
      return document

  # max documentList size is 1000 elements/ids and documents can have no more than 5120 characters
  # analyzes the sentiments of a list of documents (in our case answers), and returns the api response
  def getSentimentAnalysis(self, documents):
      response = self.client.sentiment(documents=documents)
      return response

  # analyzes one post and the corresponding answers. analyze means: "what is the sentiment score of the answers?"
  # input:
  #     the json of a stackexchange query, in the format s.t.:
  #          one item in the items list is one question with all the answers in an answer list
  # return: returns a list of posts with the corresponding sentiment analysis
  def analyzeFullPostWithAnswers(self, batch):
      multiplePostsWithAnalysis = []
      for item in batch["items"]:
          response = self.getSentimentAnalysis(self.createDocumentsList(item["answers"]))
          postWithAnalysis = {
            "question_id": item["question_id"],
            "user_id": item["owner"]["user_id"],
            "response_with_scores": self.azureResponseToJson(response)
          }
          # self.printRespons(response)
          pprint(postWithAnalysis)
          multiplePostsWithAnalysis.append(postWithAnalysis)
      
      return multiplePostsWithAnalysis
  
  # Formats the azure api response to a json object and returns it
  def azureResponseToJson(self, response):
    answer_list = []
    for document in response.documents:
        answer = {"answer_id": document.id, "sentiment_score": "{:.2f}".format(document.score)}
        answer_list.append(answer)
    
    return answer_list

  # helper function to remove code from text-/answer-body
  def remove_code_from_posts(self, raw_html):
      clean_up = re.sub("<code>.*?</code>", "", raw_html)
      return clean_up

  # helper function to remove markup from text-/answer-body
  def removeMarkUps(self, markUpText):
      cleanr = re.compile('<.*?>')
      cleantext = re.sub(cleanr, '', self.remove_code_from_posts(markUpText))
      return cleantext


sa = SentimentAnalyzer()
analyzedWithSentiments = sa.analyzeFullPostWithAnswers(sample_query_response)
pprint(analyzedWithSentiments)
