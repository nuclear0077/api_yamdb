from django.core.management.base import BaseCommand
from reviews.models import Genre, Category, TitleGenre, Title, Review, Comment
from api_yamdb.models import YamUser
import pandas as pd
import csv
from django.conf import settings
import os
from api.utils import email_is_valid

#:TODO сделать временную директорию и туда выгружать подготовленные данные чтобы не портить исходящие данные
class Command(BaseCommand):
    dict_models = {
        Genre: 'genre',
        Category: 'category',
        Title: 'titles',
        TitleGenre: 'genre_title',
        YamUser: 'users'
        # Review: 'review',
        # Comment: 'comments',
    }
    path_data = f'{settings.BASE_DIR}/static/data/'
    files_dict = {
        'category': f'{path_data}category.csv',
        'comments': f'{path_data}comments.csv',
        'genre_title': f'{path_data}genre_title.csv',
        'genre': f'{path_data}genre.csv',
        'review': f'{path_data}review.csv',
        'titles': f'{path_data}titles.csv',
        'users': f'{path_data}users.csv'
    }

    def clean_data(self):
        for model in self.dict_models.keys():
            model.objects.all().delete()
        print('Все модели очищены')

    def dir_is_exist(self, path):
        if not os.path.exists(path):
            raise FileExistsError(f'Каталог data по пути {path} не найден')
        print('Все файлы находяться в каталоге')

    def files_is_exist(self, path_files):
        for file in path_files:
            if not os.path.isfile(file):
                raise FileExistsError(f'Файл по пути {file} не найден')

    def prepare_data(self):
        genre = pd.read_csv(self.files_dict.get('genre'))
        genre.drop_duplicates(['name'], keep='first', inplace=True)
        genre.drop_duplicates(['slug'], keep='first', inplace=True)
        category = pd.read_csv(self.files_dict.get('category'))
        category.drop_duplicates(['name'], keep='first', inplace=True)
        category.drop_duplicates(['slug'], keep='first', inplace=True)
        titles = pd.read_csv(self.files_dict.get('titles'))
        if 'description' not in titles.columns:
            titles.insert(loc=3, column='description', value=None)
        titles.rename(columns={'id': 'id_titles'}, inplace=True)
        titles_columns = titles.columns
        titles.drop_duplicates(['name'], keep='first', inplace=True)
        genre_title = pd.read_csv(self.files_dict.get('genre_title'))
        genre_columns = genre_title.columns
        titles_genre = titles.merge(genre_title, how='left', left_on='id_titles', right_on='title_id')
        titles = titles_genre[titles_columns].copy()
        titles.rename(columns={'id_titles': 'id'}, inplace=True)
        titles.drop_duplicates(['id'], keep='first', inplace=True)
        titles.to_csv(self.files_dict.get('titles'), index=False)
        category.to_csv(self.files_dict.get('category'), index=False)
        titles_genre[genre_columns].to_csv(self.files_dict.get('genre_title'), index=False)
        genre.to_csv(self.files_dict.get('genre'), index=False)
        users = pd.read_csv(self.files_dict.get('users'))
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
        users.to_csv(self.files_dict.get('users'), index=False)
        print('Все данные подготовлены')

    def load_data_users(self, model, key):
        users_list = []
        with open(self.files_dict.get(key), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                if idx == 0:
                    continue
                users_list.append(YamUser(
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

    def load_data(self):
        for model, key, in self.dict_models.items():
            if key == 'users':
                self.load_data_users(model, key)
                continue
            with open(self.files_dict.get(key), newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = [model(*row) for idx, row in enumerate(reader) if idx != 0]
                model.objects.bulk_create(data)
        print('Все данные успешно загружены в БД')

    def handle(self, *args, **kwargs):
        self.clean_data()
        self.dir_is_exist(self.path_data)
        self.files_is_exist(self.files_dict.values())
        self.prepare_data()
        self.load_data()
