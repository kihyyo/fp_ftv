import re, traceback, os, difflib
from .setup import P
logger = P.logger
try:
    import tmdbsimple
except:
    try:
        os.system("pip install tmdbsimple")
        import tmdbsimple
    except Exception as e: 
        logger.error(f"Exception:{str(e)}")
        logger.error(traceback.format_exc())
from support_site import (SiteWatchaTv, SiteTmdbFtv, SiteUtil)

class tmdb(object):

    @classmethod
    def remove_special_char(cls, text):
        return re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》：]', '', text)
    
    @classmethod
    def similar(cls, seq1, seq2):
        return difflib.SequenceMatcher(a=cls.remove_special_char(seq1.lower()), b=cls.remove_special_char(seq2.lower())).ratio()

    @classmethod
    def search(cls, keyword, year=None):
        tmdb.API_KEY = 'f090bb54758cabf231fb605d3e3e0468'
        if SiteUtil.is_include_hangul(keyword):
            tmdb_search = tmdbsimple.Search().tv(query=keyword, language='ko', include_adult=True)
        else:
            tmdb_search = tmdbsimple.Search().tv(query=keyword, language='en', include_adult=True)
        tmdb_code = ''
        if tmdb_search['results'] != []:
            if year == None:
                score_list = []
                for t in tmdb_search['results']:
                    score_list.append(max(cls.similar(t['name'], keyword), cls.similar(t['original_name'], keyword))) 
                if max(score_list) > 0.7 :
                    tmdb_code = tmdb_search['results'][score_list.index(max(score_list))]['id']
            else:
                for t in tmdb_search['results']:
                    try:
                        tmdb_year = int(t['first_air_date'].split('-')[0])
                    except:
                        tmdb_year = 1900

                    if tmdb_year == int(year) :
                        tmdb_code = t['id']
                        break
                    else:
                        continue
                if tmdb_code == '':
                    tmdb_code = tmdb_search['results'][0]['id']
            return tmdb_code

        elif tmdb_search['results'] == [] and SiteUtil.is_include_hangul(keyword):
            try:
                if cls.search_watch(keyword=keyword, year=year)['ret'] == 'success':
                    cls.search(keyword=keyword, year=year)
            except:
                pass

    @classmethod
    def search_watcha(cls, keyword, year=None):
        ret = {}
        ret['ret'] == 'empty'
        watcha_ret = SiteWatchaTv.search(keyword, year=year)
        if cls.similar(keyword, watcha_ret['data'][0]['title_en']) > 0.85:
            ret['ret'] == 'success'
            en_keyword = watcha_ret['data'][0]['title_en']
        else:
            en_keyword = None
        if en_keyword is not None:
            tmdb_ret = SiteTmdbFtv.search(en_keyword, year=year)
            if tmdb_ret['ret'] == 'success':
                ret += tmdb_ret['data']
        return ret
