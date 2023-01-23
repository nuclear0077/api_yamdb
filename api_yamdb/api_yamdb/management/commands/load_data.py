from django.core.management.base import BaseCommand
from reviews.models import Genre, Category, TitleGenre, Title, Review, Comment
from api_yamdb.models import YamUser
import pandas as pd
import csv
from django.conf import settings
import os
from api.utils import email_is_valid
import logging

# :TODO сделать временную директорию и туда выгружать подготовленные данные
# чтобы не портить исходящие данные


class LoadData():
    def __init__(self):
        self.__dict_models = {
            Genre: 'genre',
            Category: 'category',
            Title: 'titles',
            TitleGenre: 'genre_title',
            YamUser: 'users',
            Review: 'review',
            Comment: 'comments',
        }
        self.__path_data = f'{settings.BASE_DIR}/static/data/'
        self.__files_dict = {
            'category': f'{self.__path_data}category.csv',
            'comments': f'{self.__path_data}comments.csv',
            'genre_title': f'{self.__path_data}genre_title.csv',
            'genre': f'{self.__path_data}genre.csv',
            'review': f'{self.__path_data}review.csv',
            'titles': f'{self.__path_data}titles.csv',
            'users': f'{self.__path_data}users.csv'
        }
        logging.debug('Конутруктор класса LoadData инициализирован')

    def __clean_data(self):
        for model in self.__dict_models.keys():
            model.objects.all().delete()
        logging.debug('Все модели очищены')

    def __dir_is_exist(self, path):
        if not os.path.exists(path):
            raise FileExistsError(f'Каталог data по пути {path} не найден')
        logging.debug('Каталог обнаружен')

    def __files_is_exist(self, path_files):
        for file in path_files:
            if not os.path.isfile(file):
                raise FileExistsError(f'Файл по пути {file} не найден')
        logging.debug('Все файлы находятся в каталоге')

    def __prepare_data(self):
        """Функция подготовки данных
            данная функция удаляет дубликаты и записи для которых нет записей
            в других таблица
            используя merge
        """
        genre = pd.read_csv(self.__files_dict.get('genre'))
        genre.drop_duplicates(['name'], keep='first', inplace=True)
        genre.drop_duplicates(['slug'], keep='first', inplace=True)
        category = pd.read_csv(self.__files_dict.get('category'))
        category.drop_duplicates(['name'], keep='first', inplace=True)
        category.drop_duplicates(['slug'], keep='first', inplace=True)
        titles = pd.read_csv(self.__files_dict.get('titles'))
        if 'description' not in titles.columns:
            titles.insert(loc=3, column='description', value=None)
        titles.rename(columns={'id': 'id_titles'}, inplace=True)
        titles_columns = titles.columns
        titles.drop_duplicates(['name'], keep='first', inplace=True)
        genre_title = pd.read_csv(self.__files_dict.get('genre_title'))
        genre_columns = genre_title.columns
        titles_genre = titles.merge(
            genre_title,
            how='inner',
            left_on='id_titles',
            right_on='title_id')
        titles = titles_genre[titles_columns].copy()
        titles.rename(columns={'id_titles': 'id'}, inplace=True)
        titles.drop_duplicates(['id'], keep='first', inplace=True)
        titles.to_csv(self.__files_dict.get('titles'), index=False)
        category.to_csv(self.__files_dict.get('category'), index=False)
        titles_genre[genre_columns].to_csv(
            self.__files_dict.get('genre_title'),
            index=False)
        genre.to_csv(self.__files_dict.get('genre'), index=False)
        users = pd.read_csv(self.__files_dict.get('users'))
        users[['is_superuser', 'is_staff', 'is_active']] = None
        allowed_roles = ['admin', 'superuser', 'moderator', 'user']
        lst_idx_to_remove = []
        for idx, row in users.iterrows():
            is_superuser = 0
            is_staff = 0
            is_active = 1
            if row['role'] not in allowed_roles:
                lst_idx_to_remove.append(idx)
                continue
            if not email_is_valid(row['email']):
                lst_idx_to_remove.append(idx)
                continue
            if row['role'] == 'admin':
                is_staff = 1
            if row['role'] == 'superuser':
                is_staff = 1
                is_superuser = 1
            users.at[idx, 'is_staff'] = is_staff
            users.at[idx, 'is_superuser'] = is_superuser
            users.at[idx, 'is_active'] = is_active
        users.drop(index=lst_idx_to_remove, inplace=True)
        users.drop_duplicates(['id'], keep='first', inplace=True)
        users.drop_duplicates(['username'], keep='first', inplace=True)
        users.drop_duplicates(['email'], keep='first', inplace=True)
        users.to_csv(self.__files_dict.get('users'), index=False)
        review = pd.read_csv(self.__files_dict.get('review'))
        review.drop_duplicates(['id'], keep='first', inplace=True)
        review.drop_duplicates(
            ['title_id', 'author'], keep='first', inplace=True)
        review = review[(
            review['score'] >= 0) & (review['score'] <= 10)]
        review_columns = review.columns
        review.rename(columns={'id': 'id_review'}, inplace=True)
        review_merge_users = review.merge(
            users, how='inner', left_on='author', right_on='id').copy()
        review_merge_users.drop(columns=['id'], inplace=True)
        review_merge_users.rename(columns={'id_review': 'id'}, inplace=True)
        review = review_merge_users[review_columns].copy()
        review.rename(columns={'id': 'id_review'}, inplace=True)
        review_titles_merge = review.merge(
            titles, how='inner', left_on='title_id', right_on='id')
        review_titles_merge.drop(columns=['id'], inplace=True)
        review_titles_merge.rename(columns={'id_review': 'id'}, inplace=True)
        review = review_titles_merge[review_columns]
        review.to_csv(self.__files_dict.get('review'), index=False)
        comments = pd.read_csv(self.__files_dict.get('comments'))
        comments.drop_duplicates(['id'], keep='first', inplace=True)
        comments.rename(columns={
            'id': 'comments_id',
            'text': 'comment_text',
            'author': 'comment_author',
            'pub_date': 'comment_pub_date'}, inplace=True)
        comments_columns = comments.columns
        comments_users_merge = comments.merge(
            users, how='inner', left_on='comment_author', right_on='id')
        comments = comments_users_merge[comments_columns].copy()
        comments_review_merge = comments.merge(
            review, how='inner', left_on='review_id', right_on='id')
        comments = comments_review_merge[comments_columns].copy()
        comments.rename(columns={
            'comments_id': 'id',
            'comment_text': 'text',
            'comment_author': 'author',
            'comment_pub_date': 'pub_date'}, inplace=True)
        comments.to_csv(self.__files_dict.get('comments'), index=False)
        logging.debug('Все данные подготовлены')

    def __load_data_users(self, model, key):
        users_list = []
        with open(self.__files_dict.get(key), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users_list.append(model(
                    id=row.get('id'),
                    username=row.get('username'),
                    email=row.get('email'),
                    bio=row.get('bio'),
                    first_name=row.get('first_name'),
                    last_name=row.get('last_name'),
                    is_superuser=row.get('is_superuser'),
                    is_staff=row.get('is_staff'),
                    is_active=row.get('is_active'),
                ))
            model.objects.bulk_create(users_list)
        return True

    def __load_data_review(self, model, key):
        users_list = []
        with open(self.__files_dict.get(key), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users_list.append(model(
                    id=row.get('id'),
                    text=row.get('text'),
                    score=row.get('score'),
                    pub_date=row.get('pub_date'),
                    author_id=row.get('author'),
                    title_id=row.get('title_id'),
                ))
                model.objects.bulk_create([
                    model(
                        id=row.get('id'),
                        text=row.get('text'),
                        score=row.get('score'),
                        pub_date=row.get('pub_date'),
                        author_id=row.get('author'),
                        title_id=row.get('title_id'),
                    )
                ])
        return True

    def __load_data(self):
        for model, key, in self.__dict_models.items():
            logging.debug(f'Загуражем данные из {self.__files_dict.get(key)} в модель {model.__name__}')
            if key == 'users':
                self.__load_data_users(model, key)
                continue
            if key == 'review':
                self.__load_data_review(model, key)
                continue
            with open(self.__files_dict.get(key), newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = [
                    model(*row) for idx, row in enumerate(reader) if idx != 0]
                model.objects.bulk_create(data)
        logging.debug('Все данные успешно загружены в БД')

    def run(self):
        self.__clean_data()
        self.__dir_is_exist(self.__path_data)
        self.__files_is_exist(self.__files_dict.values())
        self.__prepare_data()
        self.__load_data()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        load_data = LoadData()
        try:
            load_data.run()
        except Exception as exc:
            logging.exception(exc)
