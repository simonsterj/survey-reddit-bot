#!/usr/bin/python3
from copy import deepcopy
import json
import os
import praw

"""
Scrapes posts for comments and saves the comment ID and comment text to the
accompanying JSON file.
"""

JSON_DEFAULT_LOC = os.environ.get('JSON_LOCATION') or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "survey_response.json")


def login():
    """ Create a reddit instance according to praw.ini configuration.
    Call reddit.user.me() as a check.
    Return reddit instance.
    """
    print("Authenticating")
    reddit = praw.Reddit("appname", user_agent="Chrome:com.example.bot-"
                                                "name:v1 (by /u/)")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


def load_survey_responses(fp=None):
    """ Load the current survey response file as a JSON object.
    """
    if fp is None:
        fp = JSON_DEFAULT_LOC
    with open(fp, "r") as file:
        survey_results = json.load(file)
    return survey_results


def write_comments_to_file(updated_json, fp=None):
    if fp is None:
        fp = JSON_DEFAULT_LOC
    with open(fp, "w") as fp:
        json.dump(updated_json, fp)


def replace_more_comments(submission):
    submission.comments.replace_more(limit=0)
    return submission


def extract_submission_comment(submission_replaced):
    submission_comment = [{comment.id: comment.body}
                          for comment in submission_replaced.comments.list()]
    return submission_comment


def update_response(old_response, comment_to_add, sl_id):
    new_response = deepcopy(old_response)
    for i in new_response:
        if sl_id in new_response[i][0]["shortlink"]:
            new_response[i][1]["responses"] = comment_to_add
    return new_response


def prepare_survey_update(submission, sl_id, survey_responses):
    """ Combs through a submission's comments and replaces the "more comments",
    extracts the comments from the submission, and prepares file to be written
    with an updated JSON dictionary.
    """
    submission_replaced = replace_more_comments(submission)
    submission_comment = extract_submission_comment(submission_replaced)
    updated = update_response(survey_responses, submission_comment, sl_id)
    return updated


def extract_shortlink_id(survey_responses):
    """ [-6:] grabs the last six shortlink URL ID characters.
    """
    return [survey_responses[sub][0]["shortlink"][-6:]
            for sub in survey_responses]


def scrape_submissions(reddit):
    """ For each post specified in survey_responses.json, scrape the comments
    within the post and write the new or updated responses to the JSON dict.
    """
    survey_responses = load_survey_responses()
    shortlink_id_list = extract_shortlink_id(survey_responses)

    for sl_id in shortlink_id_list:
        submission = reddit.submission(id=sl_id)
        try:
            updated_responses = prepare_survey_update(submission,
                                                      sl_id,
                                                      survey_responses)
            write_comments_to_file(updated_responses)
            print("Comments from '{}' "
                  "saved to file".format(submission.subreddit))
        except OSError as e:
            print("Could not write to file: {}".format(e))


def main():
    reddit = login()
    scrape_submissions(reddit)


if __name__ == "__main__":
    main()
