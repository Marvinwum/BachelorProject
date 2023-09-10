import csv
import os
import re
import time

import praw
import prawcore.exceptions
import praw.exceptions


class Comment:
    """
    A class to represent a Reddit comment in a post
    """

    def __init__(self, text, score):
        # remove newlines and tabs from text
        self.text = re.sub(r"[\n\t]", "", text)
        self.score = score


class Post:
    """
    A class to represent a Reddit post
    """

    def __init__(self, title, score, comments):
        self.title = title
        self.score = score
        self.comments = comments


def scrape_subreddit(subreddit_name: str, num_posts: int) -> list[Post]:
    """
    Scrapes a subreddit for posts and comments
    :param subreddit_name: the name of the subreddit to scrape
    :param num_posts: the number of posts to scrape
    :return: a list of posts which each contains a list of comments
    """
    # Create a Reddit instance using the API credentials
    reddit = praw.Reddit(username="user",
                         password="password",
                         client_id="client_id",
                         client_secret="client_secret",
                         user_agent="user_agent")

    # Get the subreddit object
    subreddit = reddit.subreddit(subreddit_name)

    # Iterate through the posts in the subreddit
    posts = []

    for post in subreddit.new(limit=num_posts):

        # Fetch the comments for the post

        while True:
            try:
                post.comments.replace_more(limit=None)
                break
            except prawcore.exceptions.TooManyRequests:
                print(f"stopped due to too many requests, posts scraped: {len(posts)} out of {num_posts}")
                time.sleep(1)
            except praw.exceptions.DuplicateReplaceException:
                print(f"stopped due to duplicate replace exception, posts scraped: {len(posts)} out of {num_posts}")
                break
            except prawcore.exceptions.ServerError:
                print(f"stopped due to server error, posts scraped: {len(posts)} out of {num_posts}")
                time.sleep(1)

        comments = []
        for comment in post.comments.list():
            try:
                comments.append(Comment(comment.body, comment.score))
            except AttributeError:
                pass

        # Create a post object
        post_obj = Post(post.title, post.score, comments)
        posts.append(post_obj)

    return posts


def savetocsv(posts: list[Post], subreddit_name: str) -> None:
    """
    Saves the posts and comments to csv files
    :param posts: a list of posts which each contains a list of comments
    :param subreddit_name: the name of the subreddit, used for naming the csv files
    :return: None
    """
    # create csv file for posts
    with open(f'{subreddit_name}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["title", "score"])
        pathlength = 59
        for post in posts:
            post.title = re.sub(r'[<>:"/\\|?*]', '', post.title)
            if pathlength + len(post.title) > 240:
                print(f"post title too long: {post.title}, truncating")
                post.title = post.title[:240 - pathlength]
                print(f"truncated post title: {post.title}")
            writer.writerow([post.title, post.score])

    # select folder for comments
    if subreddit_name == "neoliberal":
        commentfolder = "neoliberal"
    elif subreddit_name == "conservative":
        commentfolder = "conservative"
    else:
        commentfolder = "politics"

    try:
        os.mkdir(commentfolder)
    except OSError:
        pass

    # create csv files for comments
    for post in posts:

        try:
            with open(f'{commentfolder}/{post.title}.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["text", "score"])

                for comment in post.comments:
                    writer.writerow([comment.text, comment.score])
        except OSError:
            print(f"could not find comment: {post.title}, skipping")
            pass


savetocsv(posts=scrape_subreddit(subreddit_name="neoliberal", num_posts=1000), subreddit_name="neoliberal")

savetocsv(posts=scrape_subreddit(subreddit_name="conservative", num_posts=1000), subreddit_name="conservative")

savetocsv(posts=scrape_subreddit(subreddit_name="politics", num_posts=1000), subreddit_name="politics")
