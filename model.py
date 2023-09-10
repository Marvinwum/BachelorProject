import nltk
import pandas as pd
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))


def preprocess_text(text: str) -> str:
    """
    Preprocesses a string of text by converting it to lowercase, removing punctuation, removing stopwords, and applying
    stemming
    :param text: the text to preprocess
    :return: the preprocessed text
    """
    text = text.lower()  # Convert to lowercase
    text = ''.join([char for char in text if char not in string.punctuation])  # Remove punctuation
    tokens = text.split()  # Tokenize using simple split
    filtered_tokens = [token for token in tokens if token not in stop_words]  # Remove stopwords

    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]  # Apply stemming
    return ' '.join(stemmed_tokens)


def train_model(training_data: str) -> tuple[LogisticRegression, TfidfVectorizer]:
    """
    Trains a Logistic Regression model to classify text as either 'Conservative' or 'Liberal'
    :param training_data: the path to the training data, containing a column named Conservative and a column named
    Liberal
    :return: a tuple containing the trained Logistic Regression model and the TF-IDF Matrix containing the features of
    the training data
    """
    # Load Training Data
    data = pd.read_excel(training_data)

    # Reformat Data into a DataFrame with two columns: 'Text' and 'Label'
    republican_df = data[['Conservative']].copy()
    republican_df.columns = ['Text']
    republican_df['Label'] = 'Conservative'
    democrat_df = data[['Liberal']].dropna().copy()
    democrat_df.columns = ['Text']
    democrat_df['Label'] = 'Liberal'
    formatted_data = pd.concat([republican_df, democrat_df], axis=0).reset_index(drop=True)

    # Preprocess and Split Data into Training and Testing Sets
    formatted_data['Processed_Text'] = formatted_data['Text'].apply(preprocess_text)
    X_train, X_test, y_train, y_test = train_test_split(formatted_data['Processed_Text'],
                                                        formatted_data['Label'],
                                                        test_size=0.2,
                                                        stratify=formatted_data['Label'],
                                                        random_state=22)

    # TF-IDF Vectorization
    tfidf_vectorizer = TfidfVectorizer(max_features=5000)
    X_train = tfidf_vectorizer.fit_transform(X_train)
    X_test = tfidf_vectorizer.transform(X_test)

    # Train Model
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    # Evaluate Accuracy
    print("Model Accuracy:", clf.score(X_test, y_test))
    return clf, tfidf_vectorizer


def predict(input: str, clf: LogisticRegression, tfidf_vectorizer: TfidfVectorizer) -> None:
    """
    Predicts the labels of the new data and saves the results to a CSV file
    :param input: the path to the new data
    :param clf: the trained Logistic Regression model
    :param tfidf_vectorizer: the TF-IDF Matrix containing the features of the training data
    :return: None
    """
    # Load New Data for Classification
    new_data = pd.read_csv(input)
    new_data['Processed_Text'] = new_data['title'].apply(preprocess_text)

    # Vectorize and Predict
    X_neoliberal = tfidf_vectorizer.transform(new_data['Processed_Text'])
    new_data['Predicted_Label'] = clf.predict(X_neoliberal)

    # Remove the 'Processed_Text' column
    new_data = new_data.drop('Processed_Text', axis=1)

    new_data.to_csv(input, index=False)
    print("Predictions saved!")


model, matrix = train_model("trainingData.xlsx")
predict("politics.csv", model, matrix)
