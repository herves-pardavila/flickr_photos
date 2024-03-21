# -*- coding: utf-8 -*-
"""
Script for computing the photo-user-days and visitation rates out of flickr photographs

@author: David Herves Pardavila
"""

import pandas as pd
import geopandas as gpd
import io
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
class FlickrPhotos():
    def __init__(self,path):
        df=pd.read_csv(path)
        df.date=pd.to_datetime(df.date)
        # df["year"]=df.date.dt.year
        # df["month"]=df.date.dt.month
        # df["day_of_week"]=df.date.dt.dayofweek
        # df["day_of_year"]=df.date.dt.dayofyear
        self.df=df
        self.df.date=self.df.date.astype(str)
        gdf=gpd.GeoDataFrame(data=self.df,crs="EPSG:4326",geometry=gpd.points_from_xy(self.df.longitude,self.df.latitude))
        self.gdf=gdf
    def save_geo_file(self,output_file):
        self.gdf.to_file(output_file,index=False)

    def save_dataframe(self,output_file):
        self.df.to_csv(output_file)

    def clip(self,area_of_interest):
        mask=gpd.read_file(area_of_interest)
        if mask.crs != self.gdf.crs:
            self.gdf.to_crs(mask.crs,inplace=True)
        self.gdf=self.gdf.clip(mask)
        self.df=self.gdf

    def plot(self):
        self.gdf.plot()
        plt.show()

    def print_general_info(self):
        print("Total number of photos",len(self.df))
        print("Total number of owners=",len(self.df.owner.unique()))
        print("Percent of photos whitout owner=",self.df.owner.isna().sum()/len(self.df))
        print("Percent of photos without date=",self.df.date.isna().sum()/len(self.df))
        print("Percent of photos wihtout coordinates=",self.df.latitude.isna().sum()/len(self.df))
        print("Percent of photos without any tags=", self.df.tags.isna().sum()/len(self.df))
        print("Percent of photos without Title=", self.df.Title.isna().sum()/len(self.df))

    def get_tags(self,df):
        tagged=df[df.tags.notna()]
        fun= lambda x : x.split()
        fun= lambda x : x.split()
        tags=list(map(fun,tagged.tags))
        flattened = [val for sublist in tags for val in sublist]
        return flattened
    
    def get_title_words(self,df):
        tagged=df[df.Title.notna()]
        fun= lambda x : x.split()
        fun= lambda x : x.split()
        tags=list(map(fun,tagged.Title))
        flattened = [val for sublist in tags for val in sublist]
        return flattened

    def word_cloud(self,words):
        for i in range(len(words)):
            words[i] = words[i].lower()
        comment_words = ''
        comment_words += " ".join(words)+" "
        stopwords=set(STOPWORDS)
        stopwords.update(["o","os","a","as","do","dos","da","das","el","los","la","las","de","e"])
        wordcloud = WordCloud(width= 800, height = 800, stopwords=stopwords,min_font_size=15).generate(comment_words)

    
        fig=plt.figure()
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.show()
        return
    
    def word_count(self,words):
        """
        Word Counter

        Given an body of text, return a hash table of the frequency of
        each word.

        ..  warnings::

            - Capital and lower case versions of the same word should be counted

        as the same word.

            - Remove punctuations from all words.

        ..  note::


        Where N is the number of characters in the string.

            - Time: O(N)

            - Space: O(N)

        :Example:

        >>> word_count('The cat and the hat.')
        {'the': 2, 'cat': 1, 'and': 1, 'hat': 1}
        >>> word_count('As soon as possible.')
        {'as': 2, 'soon': 1, 'possible': 1}
        >>> word_count("It's a man, it's a plane, it's superman!")
        {'its': 3, 'a': 2, 'man': 1, 'plane': 1, 'superman': 1}

        :param sentence: Input string
        :type sentence: str

        :return: Returns hash-table of frequence of each word in input
        :rtype: dict
        """
        for i in range(len(words)):
            words[i] = words[i].lower()
        sentence = ''
        sentence += " ".join(words)+" "
        translate = sentence.maketrans({char: None for char in "'.,:*!"})
        cleaned_words = sentence.lower().translate(translate).split()
        word_counter = {}
        for word in cleaned_words:
            if word in word_counter:
                word_counter[word] += 1
            else:
                word_counter[word] = 1
        
        
        dataframe=pd.DataFrame.from_dict(word_counter,orient="index",columns=["Count"])
        dataframe.sort_values(by="Count",ascending=False,inplace=True)

        return dataframe
    
    def author_information(self,threshold):
        authors=self.df.owner_name.unique()
        df=pd.DataFrame()
        for author in authors:
            newdf=self.df[self.df.owner_name==author]
            photos=len(newdf)
            tags=self.get_tags(newdf)
            tags=self.word_count(tags)
            tags=str(list(tags.index))
            titles=self.get_title_words(newdf)
            titles=self.word_count(titles)
            titles=str(list(titles.index))
            df=pd.concat([df,pd.DataFrame(data={"Name":author,"Photos":photos,"tags":tags,"title_words":titles},index=[0])])
        df=df.reset_index()
        df.sort_values(by="Photos",inplace=True)
        df=df[df.Photos > threshold]
        return df


    def delete_users(self,user_names):

        self.df=self.df[~self.df.owner_name.isin(user_names)]
        
    
        return self.df
    def delete_tags(self,tags):
        

        delete=[True]*len(self.df)
        for i in range(len(self.df)):
            
            mydf=self.df.iloc[i]
            try:
                tagsi=mydf.tags.split()
                if any(x in tagsi for x in tags):
                    delete[i]=False
            except AttributeError : continue
            
        self.df=self.df[delete]
        return self.df
    
    def delete_titles(self,titles):

        delete=[True]*len(self.df)
        for i in range(len(self.df)):
            
            mydf=self.df.iloc[i]
            try:
                titlesi=mydf.Title.split()
                if any(x in titlesi for x in titles):
                    delete[i]=False
            except AttributeError : continue
            
        self.df=self.df[delete]
        return self.df
    def photo_user(self):
        """Computes photo-user. This is the number of users that have uploaded to flickr at leat one picture in a point of space  at a given day.
        This fucntion will delete photos which any of these information is missing: owner, data, location. As well as two (or more) photos uploaded by 
        the same owner the same day in the same location. As location is a point of space, this is very unlikely to happen

        Args:
            df (pandas.DataFrame): database with the flickr photos after being prepared by the function prepare_database

        Returns:
            new (pandas.DataFrame): output of the funtion
        """

        df2=self.df[self.df.owner.isna()==False] #delete photos with no owner
        df2.loc[:,"photo-count"]=1
        new=df2.groupby(["date","owner","latitude","longitude"],as_index=False).mean(numeric_only=True)
        
        return new
    
    def photo_user_days(self,photo_users,gridded_aoi,fid_column):
        """Computes photo-user-days for a gridded ara of interest with cells. For each cell and day, photo-user-days is the
        number of owners, that have uploaded at least one photo.

        Args:
            photo_user_file (str): Path to the photo-user shapefile with the point data
            gridded_aoi (str): Path to the girdded area of interest vectorial file
            fid_column(str): Name of the column in the gridded_aoi shapefile with the identifiers of the polygons 

        Returns:
            _type_: _description_
        """

        
        geopu=gpd.GeoDataFrame(photo_users,crs="EPSG:4326",geometry=gpd.points_from_xy(photo_users.longitude,photo_users.latitude))
        geopu.to_crs(gridded_aoi.crs,inplace=True)
        geopu=gpd.sjoin(gridded_aoi,geopu,how="left")
        geopu.loc[geopu["photo-count"].isna(),"photo-count"]=0
        #geopu.loc[geopu["year"].isna(),"year"]=2020
        #geopu.loc[geopu["day_of_year"].isna(),"day_of_year"]=1
        #geopu.loc[geopu["owner"].isna(),"owner"]=0
        geopu["date"]=pd.to_datetime(geopu.date)
        geopu["Date"]=geopu.date.dt.date
        pud=geopu.groupby([fid_column,"Date","owner"],as_index=False).mean(numeric_only=True)
        pud=pud.groupby([fid_column,"Date"],as_index=False).sum(numeric_only=True)
        
        pud.rename(columns={"photo-count":"PUD"},inplace=True)
        #pud["date"]=pd.to_datetime(pud.year*1000+pud.day_of_year,format="%Y%j")
        #pud.date=pud.date.astype(str)
        #pud=pud[["FID","date","PUD"]]
        
 
        return pud 
        
        


# def prepare_database(shapefile):
#     """_summary_

#     Args:
#         shapefile (str): Path to the shapefile with the info of the flickr photos database. This shapefile 
#         was created in QGIS joining the different layers obtained by Pablo and Ana
#     return
#         df (pandas.DataFrame): Pandas Data Frame with the new created columns and all the previous information
#         stored in the shapefile. 
#     """
#     gdf=gpd.read_file(shapefile)
#     print(gdf)
#     gdf=pd.DataFrame(gdf) 
#     #we set the column with information about the date to pandas.datetime format
#     gdf.date=pd.to_datetime(gdf.date,errors="coerce")
#     #functions for extracting year, month, days 
#     fun_años= lambda x : x.year
#     fun_mes= lambda x : x.month
#     fun_dia_mes= lambda x : x.day
#     fun_dia_año= lambda x: x.dayofyear
#     fun_dia_semana= lambda x: x.dayofweek
#     #we create new columns with info of year, month, date
#     gdf["year"]=list(map(fun_años,gdf.date))
#     gdf["month"]=list(map(fun_mes,gdf.date))
#     gdf["day"]=list(map(fun_dia_mes,gdf.date))
#     gdf["day_of_year"]=list(map(fun_dia_año,gdf.date))
#     gdf["day_of_week"]=list(map(fun_dia_semana,gdf.date))
#     #summaty statistics
#     print(gdf.describe())
#     print(gdf.info())
#     gdf.to_csv("flickr_photos.csv",index=False)
#     info=save_info(gdf)
#     info.to_csv("info_flickr_photos.csv",index=False)
#     description=gdf.describe()
#     description=description.round(decimals=2)
#     description.to_csv("description_flickr_photos.csv")
#     return gdf
# def save_info(df):
#     buffer = io.StringIO()
#     df.info(buf=buffer)
#     lines = buffer.getvalue().splitlines()
#     df = (pd.DataFrame([x.split() for x in lines[5:-2]], columns=lines[3].split()).drop('Count',axis=1).rename(columns={'Non-Null':'Non-Null Count'}))
#     return df


# def reindex_dataframe(df,spatial_column,date_column,other_columns,start,end):
#     #we get the indentiers of the spatial units
#     values=df[spatial_column].unique()
#     df2=pd.DataFrame()
#     t=pd.date_range(start,end)
#     for value in values:
#         print(value)
#         newdf=df[df[spatial_column]==value]
#         #
#         #we delete duplicated dates, if they do exist
#         newdf.drop_duplicates(date_column,inplace=True)
#         #sorting dates
#         newdf.sort_values(date_column,inplace=True)
#         #reindexing
#         newdf.set_index(date_column,inplace=True)
#         newdf=newdf.reindex(t)
#         #recovering old index
#         newdf[date_column]=newdf.index
#         newdf.reset_index(inplace=True,drop=True)
#         #we set in the new created rows the identifiers of the spatial unit 
#         newdf[spatial_column]=value
#         #and we set in the new created rows the values of other columns.
#         for column in other_columns:
#             id=int(newdf[column].unique())
#             newdf[column]=id
#         df2=pd.concat([df2,newdf])
#     return df2



if __name__ =="__main__":
    
    con=FlickrPhotos("INE/ine_comparison_cleaned.csv")
    pu=con.photo_user()
    aoi=gpd.read_file("qgis/griddedaoi.shp")
    print(aoi)
    geopud=con.photo_user_days(pu,aoi)
    print(geopud)
    print(geopud.PUD.unique())
