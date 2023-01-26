import csv
import logging
import os
import shutil
from datetime import datetime
import pandas as pd
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews.models import Genre, Category, TitleGenre, Title, Review, Comment
from users.models import User
from core.utils import email_is_valid

MODELS = {
    Genre: 'genre',
    Category: 'category',
    Title: 'titles',
    TitleGenre: 'genre_title',
    User: 'users',
    Review: 'review',
    Comment: 'comments',
}

PATH_FILES = {
    'category': Path(settings.PATH_DATA, 'category.csv'),
    'comments': Path(settings.PATH_DATA, 'comments.csv'),
    'genre_title': Path(settings.PATH_DATA, 'genre_title.csv'),
    'genre': Path(settings.PATH_DATA, 'genre.csv'),
    'review': Path(settings.PATH_DATA, 'review.csv'),
    'titles': Path(settings.PATH_DATA, 'titles.csv'),
    'users': Path(settings.PATH_DATA, 'users.csv')
}


class Data:
    def __dir_is_exist(self, path):
        if not os.path.exists(path):
            raise FileExistsError(f'Каталог data по пути {path} не найден')
        logging.debug('Каталог обнаружен')

    def __files_is_exist(self, path_files):
        for file in path_files:
            if not os.path.isfile(file):
                raise FileExistsError(f'Файл по пути {file} не найден')
        logging.debug('Все файлы находятся в каталоге')

    def __get_csv_file(self):
        files_csv = []
        logging.debug(f'Получим список файлов csv'
                      f' в каталоге {settings.PATH_DATA}')
        for root, dirs, files in os.walk(settings.PATH_DATA):
            for filename in files:
                if filename.endswith('csv'):
                    files_csv.append(filename)
        logging.debug(f'Список файлов {files_csv}')
        return files_csv

    def __create_dir_for_original(self):
        name_catalog = datetime.now().strftime("%d%m%Y%H%M%S")
        path_dir = Path(settings.PATH_DATA, name_catalog)
        os.mkdir(path_dir)
        logging.debug(f'Была создана папка для'
                      f'копирования оригиналов csv {path_dir}')
        return name_catalog

    def __copy_original(self, list_fiels, dst):
        for file in list_fiels:
            src_file_name = Path(settings.PATH_DATA, file)
            dst_file_name = Path(settings.PATH_DATA, dst, file)
            logging.debug(f'Копируем файл {file} из'
                          'f{settings.PATH_DATA} в {dst_file_name}')
            shutil.copy(src_file_name, dst_file_name, follow_symlinks=True)
        return True

    def __prepare_genre(self):
        logging.debug('Подготавливаем genre')
        genre = pd.read_csv(PATH_FILES.get('genre'))
        genre.drop_duplicates(['name'], keep='first', inplace=True)
        genre.drop_duplicates(['slug'], keep='first', inplace=True)
        genre.to_csv(PATH_FILES.get('genre'), index=False)
        return True

    def __prepare_category(self):
        logging.debug('Подготавливаем category')
        category = pd.read_csv(PATH_FILES.get('category'))
        category.drop_duplicates(['name'], keep='first', inplace=True)
        category.drop_duplicates(['slug'], keep='first', inplace=True)
        category.to_csv(PATH_FILES.get('category'), index=False)
        return True

    def __prepare_titles_and_genre_title(self):
        logging.debug('Подготавливаем titles и titles_genre')
        titles = pd.read_csv(PATH_FILES.get('titles'))
        if 'description' not in titles.columns:
            titles.insert(loc=3, column='description', value=None)
        titles.rename(columns={'id': 'id_titles'}, inplace=True)
        titles_columns = titles.columns
        titles.drop_duplicates(['name'], keep='first', inplace=True)
        genre_title = pd.read_csv(PATH_FILES.get('genre_title'))
        genre_columns = genre_title.columns
        titles_genre = titles.merge(
            genre_title,
            how='inner',
            left_on='id_titles',
            right_on='title_id')
        titles = titles_genre[titles_columns].copy()
        titles.rename(columns={'id_titles': 'id'}, inplace=True)
        titles.drop_duplicates(['id'], keep='first', inplace=True)
        titles.to_csv(PATH_FILES.get('titles'), index=False)
        titles_genre[genre_columns].to_csv(
            PATH_FILES.get('genre_title'),
            index=False)
        return True

    def __prepare_users(slef):
        logging.debug('Подготавливаем users')
        users = pd.read_csv(PATH_FILES.get('users'))
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
        users.to_csv(PATH_FILES.get('users'), index=False)
        return True

    def __prepare_review(self):
        logging.debug('Подготавливаем review')
        users = pd.read_csv(PATH_FILES.get('users'))
        titles = pd.read_csv(PATH_FILES.get('titles'))
        review = pd.read_csv(PATH_FILES.get('review'))
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
        review.to_csv(PATH_FILES.get('review'), index=False)
        return True

    def __prepare_comments(self):
        users = pd.read_csv(PATH_FILES.get('users'))
        review = pd.read_csv(PATH_FILES.get('review'))
        comments = pd.read_csv(PATH_FILES.get('comments'))
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
        comments.to_csv(PATH_FILES.get('comments'), index=False)
        return True

    def __prepare_data(self):
        self.__prepare_genre()
        self.__prepare_category()
        self.__prepare_titles_and_genre_title()
        self.__prepare_users()
        self.__prepare_review()
        self.__prepare_comments()
        logging.debug('Все данные подготовлены')

    def run(self):
        self.__dir_is_exist(settings.PATH_DATA)
        self.__files_is_exist(PATH_FILES.values())
        list_files = self.__get_csv_file()
        dst_dir = self.__create_dir_for_original()
        self.__copy_original(list_files, dst_dir)
        self.__prepare_data()


class LoadData:
    def __clean_data(self):
        for model in MODELS.keys():
            model.objects.all().delete()
        logging.debug('Все модели очищены')

    def __load_data_users(self, model, key):
        users_list = []
        with open(PATH_FILES.get(key), newline='') as csvfile:
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
        with open(PATH_FILES.get(key), newline='') as csvfile:
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
        for model, key, in MODELS.items():
            logging.debug(
                f'Загуражем данные из {PATH_FILES.get(key)}'
                f'в модель {model.__name__}')
            if key == 'users':
                self.__load_data_users(model, key)
                continue
            if key == 'review':
                self.__load_data_review(model, key)
                continue
            with open(PATH_FILES.get(key), newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = [
                    model(*row) for idx, row in enumerate(reader) if idx != 0]
                model.objects.bulk_create(data)
        logging.debug('Все данные успешно загружены в БД')

    def run(self):
        self.__clean_data()
        self.__load_data()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        data = Data()
        load_data = LoadData()
        try:
            data.run()
            load_data.run()
        except Exception as exc:
            logging.exception(exc)
