# Copyright 2019, Lukas Jäger 
#
# This file is part of Brewdie.
#
# Brewdie is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Brewdie is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Brewdie.  If not, see <http://www.gnu.org/licenses/>. 

import sqlite3
import sys
from recipe import *

class BrewdieDB:
    def __init__(self):
        try:
            # Establishing a connection
            connection = sqlite3.connect('brewdie.db')
            cursor = connection.cursor()

            # Querying for existing tables
            table_names = []
            for row in cursor.execute('SELECT name FROM sqlite_master WHERE type=\'table\''):
                table_names.append(row[0])

            # Creating tables if they don't exist
            if not 'Recipes' in table_names:
                cursor.execute('CREATE TABLE Recipes (name TEXT PRIMARY KEY, type TEXT, boiling_minutes INTEGER)')
            if not 'Malts' in table_names:
                cursor.execute('CREATE TABLE Malts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, gramms REAL, recipe_name TEXT)')
            if not 'Rests' in table_names:
                cursor.execute('CREATE TABLE Rests (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, degrees REAL, minutes INTEGER, position INTEGER, recipe_name TEXT)')
            if not 'HopDosages' in table_names:
                cursor.execute('CREATE TABLE HopDosages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, minutes INTEGER, gramms REAL, recipe_name TEXT)')

            connection.commit()
        
        except sqlite3.Error as e:
            if connection:
                connection.rollback()
                sys.exit(1)

        finally:
            if connection:
                connection.close()

    def store_recipe(self, recipe):
        try:
            # Establishing a connection
            connection = sqlite3.connect('brewdie.db')
            cursor = connection.cursor()
        
            # Querying, whether or not the recipe is already in the database
            recipe_names = []
            for row in cursor.execute('SELECT name FROM Recipes'):
                recipe_names.append(row[0])
            if recipe.name in recipe_names:
                print("Recipe is already stored in the database")
            else:
                # It is not, so we can insert it
                cursor.execute('INSERT INTO Recipes VALUES(?, ?, ?)', (recipe.name, recipe.style, recipe.boiling_minutes))
                for (malt_name, malt_gramms) in recipe.malts.items():
                    cursor.execute('INSERT INTO Malts(name, gramms, recipe_name) VALUES(?, ?, ?)', (malt_name, malt_gramms, recipe.name))

                index = 0
                for rest in recipe.rests:
                    cursor.execute('INSERT INTO Rests(name, degrees, minutes, position, recipe_name) VALUES(?, ?, ?, ?, ?)', (rest.name, rest.degrees, rest.minutes, index, recipe.name))
                    index = index + 1

                for hop_dosage in recipe.hop_dosages:
                    cursor.execute('INSERT INTO HopDosages(name, minutes, gramms, recipe_name) VALUES(?, ?, ?, ?)', (hop_dosage.name, hop_dosage.minutes, hop_dosage.gramms, recipe.name))
            connection.commit()
        except sqlite3.Error as e:
            print("Something went wrong")
            print(e)
            if connection:
                connection.rollback()
            return

        finally:
            if connection:
                connection.close()

    def load_recipes(self):
        recipes = []
        try:
            # Establishing a connection
            connection = sqlite3.connect('brewdie.db')
            cursor = connection.cursor()
        
            # Getting all the recipes
            for row in cursor.execute('SELECT * FROM Recipes'):
                # Converting a recipe database row into a python object
                recipe = Recipe(row[0], row[1], row[2])

                # Adding the malts
                for malt_row in cursor.execute('SELECT * FROM Malts WHERE recipe_name=\'%s\'' % recipe.name):
                    recipe.malts[malt_row[1]] = malt_row[2]

                # Adding the rests
                for rest_row in cursor.execute('SELECT * FROM Rests WHERE recipe_name=\'%s\' ORDER BY position ASC' % recipe.name):
                    recipe.rests.append(Rest(rest_row[1], rest_row[2], rest_row[3]))

                # Adding the hop dosages
                for hop_dosage_row in cursor.execute('SELECT * FROM HopDosages WHERE recipe_name=\'%s\'' % recipe.name):
                    recipe.hop_dosages.append(HopDosage(hop_dosage_row[1], hop_dosage_row[3], hop_dosage_row[2]))

                # Adding the recipe to the list of recipes
                recipes.append(recipe)

        except sqlite3.Error as e:
            print("Something went wrong")
            print(e)
            if connection:
                connection.rollback()
            return

        finally:
            if connection:
                connection.close()
        return recipes
