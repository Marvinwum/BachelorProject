import csv
import os
import pandas as pd


def csvtotxt(csvfile: str, txtfile: str) -> None:
    """
    Converts the first column of a csv file to a text file for use in sentistrength
    :param csvfile: the csv file to convert
    :param txtfile: the text file to write to
    :return: None
    """
    with open(csvfile, 'r', encoding='utf-8') as csvin:
        reader = csv.reader(csvin)
        lines = [row[0] for row in reader]

        # Write the values to a text file
        with open(txtfile, 'w', encoding='utf-8') as text_file:
            if lines.__len__() == 1:
                # If there are no comments, add a dummy value for sentistrength (0 doesn't change the sentiment)
                lines.append("0")
            for value in lines:
                value = value.replace('\n', ' ')
                text_file.write(value + '\n')


def createcommenttxt(subreddit_name: str) -> None:
    """
    converts all csv files in a folder to text files for use in sentistrength
    :param subreddit_name: the name of the folder to convert
    :return: None
    """
    if subreddit_name == "neoliberal":
        commentfolder = "neoliberaltxt"
    elif subreddit_name == "conservative":
        commentfolder = "conservativetxt"
    else:
        commentfolder = "politicstxt"

    try:
        os.mkdir(commentfolder)
    except OSError:
        pass

    for filename in os.listdir(subreddit_name):
        csvtotxt(f"{subreddit_name}/{filename}", f"{commentfolder}/{filename[:-4]}.txt")


def getsentiment(file: str) -> tuple[list[int], list[int]]:
    """
    extracts the sentiment values for each comment from a text file
    :param file: the text file to extract the sentiment values from
    :return: a tuple containing a list of positive sentiment values and a list of negative sentiment values
    """
    positive_sentiment_list = []
    negative_sentiment_list = []

    # Open the text file
    with open(file, 'r', encoding='utf-8') as text_file:
        lines = text_file.readlines()
        if lines.__len__() == 0:
            return [1], [-1]
        for line in lines:
            # Find the sentiment values, separated by a tab
            sentimentlocation = line.find("\t")
            sentiment = line[sentimentlocation + 1:]

            positive_sentiment = int(sentiment[0:sentiment.find("\t")])

            sentiment = sentiment[sentiment.find("\t") + 1:]
            negative_sentiment = int(sentiment)

            # Add the sentiment values to the lists
            positive_sentiment_list.append(positive_sentiment)
            negative_sentiment_list.append(negative_sentiment)

    return positive_sentiment_list, negative_sentiment_list


def add_sentiment_to_csv(sentiment: tuple, commentname: str, foldername: str) -> None:
    """
    adds the sentiment values as columns for each comment in a comment csv file
    :param sentiment: a tuple containing the positive and negative sentiment values
    :param commentname: the name of the comment csv file
    :param foldername: the folder the comment csv file is in
    :return: None
    """

    positive_sentiment_list, negative_sentiment_list = sentiment
    csv_input = pd.read_csv(f'{foldername}/{commentname}.csv')

    # fix issue with rare extra rows in csv file from sentistrength
    if len(csv_input) > len(positive_sentiment_list):
        csv_input = csv_input.iloc[:len(positive_sentiment_list)]
        print(f"trimmed {commentname}.csv")

    csv_input['positiveSentiment'] = positive_sentiment_list
    csv_input['negativeSentiment'] = negative_sentiment_list
    csv_input.to_csv(f'{foldername}/{commentname}.csv', index=False)


def changefilenames(foldername: str) -> None:
    """
    removes unnecessary characters from the filenames from sentistrength
    :param foldername: the folder to change the filenames of
    :return: None
    """
    for filename in os.listdir(foldername):
        os.rename(f"{foldername}/{filename}", f"{foldername}/{filename[:-12]}.txt")


def add_sentiment_to_folder(foldername: str) -> None:
    """
    adds the sentiment values as columns for each comment in every post csv file in a folder
    :param foldername: the folder to add the sentiment values to
    :return: None
    """
    txtfoldername = foldername + "txt"
    for filename in os.listdir(txtfoldername):
        sentiment = getsentiment(f"{txtfoldername}/{filename}")
        add_sentiment_to_csv(sentiment, filename[:-4], foldername)


def getaverages(filename: str) -> tuple[float, float, float]:
    """
    gets the average sentiment values and scores for each post
    :param filename: the name of the csv file to get the averages from
    :return: a tuple containing the average score, positive sentiment, and negative sentiment
    """
    try:
        csv_input = pd.read_csv(filename)
    except FileNotFoundError:
        csv_input = pd.read_csv(filename.replace("\u200b", ""))
    score = round(csv_input['score'].mean(), 2)
    positive_sentiment = round(csv_input['positiveSentiment'].mean(), 2)
    negative_sentiment = round(csv_input['negativeSentiment'].mean(), 2)
    return score, positive_sentiment, negative_sentiment


def add_averages_to_post(filename: str) -> None:
    """
    adds the average sentiment values and scores to the post csv file
    :param filename: the name of the csv file to add the averages to
    :return: None
    """
    folder = filename[:-4]
    scores = []
    positive_sentiments = []
    negative_sentiments = []
    with open(filename, 'r', encoding='utf-8') as csvin:
        reader = csv.reader(csvin)
        lines = [row[0] for row in reader]
        lines = lines[1:]

        for line in lines:

            comment = line + ".csv"
            score, positive_sentiment, negative_sentiment = getaverages(f"{folder}/{comment}")

            # check if the score is NaN (not a number). If it is, set it to 0
            if score != score:
                score = 0

            scores.append(score)
            positive_sentiments.append(positive_sentiment)
            negative_sentiments.append(negative_sentiment)

    csv_input = pd.read_csv(filename)
    csv_input['avgCommentScore'] = scores
    csv_input['avgPositiveSentiment'] = positive_sentiments
    csv_input['avgNegativeSentiment'] = negative_sentiments
    csv_input.to_csv(filename, index=False)


def add_acceptance(filename: str) -> None:
    """
    adds the acceptance scores to the post csv file
    :param filename: the name of the csv file to add the acceptance scores to
    :return: None
    """
    # Load the CSV from the provided path
    df = pd.read_csv(filename)

    # find the maximum score
    score_max = df['score'].max()

    # calculate the acceptance score
    df['Acceptance'] = (df['score'] / score_max +
                        (df['avgPositiveSentiment'] - 1) / 4 +
                        (df['avgNegativeSentiment'] + 5) / 4) / 3

    # Save the DataFrame back to the same CSV path
    df.to_csv(filename, index=False)


def add_sentiment_to_comments(folder: str):
    """
    adds the sentiment values as columns for each comment in every post csv file in a folder
    :return: None
    """
    createcommenttxt(folder)
    files = os.listdir(folder + "txt")
    input("please run sentistrength on txt folder")
    # Delete the files that don't contain results
    for file in files:
        os.remove(f"{folder}txt/{file}")
    changefilenames(folder + "txt")
    add_sentiment_to_folder(folder)

    # Delete the txt folder
    for file in files:
        os.remove(f"{folder}txt/{file}")
    os.rmdir(folder + "txt")


add_sentiment_to_comments("politics")

add_averages_to_post("politics.csv")

add_acceptance("politics.csv")
