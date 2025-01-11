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
    def search(cls, keyword, year=None, meta_cache={}, searched_keywords=None):
        tmdb.API_KEY = 'f090bb54758cabf231fb605d3e3e0468'

        if searched_keywords is None:
            searched_keywords = set()
        
        if keyword in searched_keywords:
            return '' 

        searched_keywords.add(keyword)
    
        if keyword in meta_cache:
            return meta_cache[keyword]

        language = 'ko' if SiteUtil.is_include_hangul(keyword) else 'en'
        tmdb_search = tmdbsimple.Search().tv(query=keyword, language=language, include_adult=True)
    
        if tmdb_search['results']:
            if year is None:
                score_list = [
                    max(cls.similar(t['name'], keyword), cls.similar(t['original_name'], keyword))
                    for t in tmdb_search['results']
                ]
                if max(score_list) > 0.7:
                    tmdb_code = tmdb_search['results'][score_list.index(max(score_list))]['id']
                else:
                    tmdb_code = tmdb_search['results'][0]['id']
            else:
                tmdb_code = ''
                for t in tmdb_search['results']:
                    try:
                        tmdb_year = int(t['first_air_date'].split('-')[0])
                    except:
                        tmdb_year = 1900
    
                    if tmdb_year == int(year):
                        tmdb_code = t['id']
                        break
                if not tmdb_code:
                    tmdb_code = tmdb_search['results'][0]['id']
        else:
            try:
                watch_result = cls.search_watch(keyword=keyword, year=year)
                if watch_result.get('ret') == 'success':
                    new_keyword = watch_result.get('updated_keyword', keyword)
                    return cls.search(new_keyword, year, meta_cache, searched_keywords) 
            except:
                pass
            tmdb_code = ''  
    
        meta_cache[keyword] = tmdb_code
        return tmdb_code

    @classmethod
    def search_watcha(cls, keyword, year=None):
        ret = {'ret': 'empty', 'data': None}
        watcha_ret = SiteWatchaTv.search(keyword, year=year)
        if watcha_ret and cls.similar(keyword, watcha_ret['data'][0]['title_en']) > 0.85:
            ret['ret'] = 'success'
            en_keyword = watcha_ret['data'][0]['title_en']
            if en_keyword:
                tmdb_ret = SiteTmdbFtv.search(en_keyword, year=year)
                if tmdb_ret['ret'] == 'success':
                    ret['data'] = tmdb_ret['data']
        return ret

