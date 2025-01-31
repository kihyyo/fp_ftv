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
    def search(cls, keyword, year=None, meta_cache={}):

        tmdb.API_KEY = 'f090bb54758cabf231fb605d3e3e0468'

        cache_key = (keyword, year)

        if cache_key in meta_cache:
            return meta_cache[cache_key]

        lang = 'ko' if SiteUtil.is_include_hangul(keyword) else 'en'
        tmdb_search = tmdbsimple.Search().tv(query=keyword, language=lang, include_adult=True)

        tmdb_code = ''
        if tmdb_search['results'] :
            results = tmdb_search['results']
            if year == None:
                score_list = []
                for t in tmdb_search['results']:
                    score_list.append(
                        max(cls.similar(t.get(name, ''), keyword), cls.similar(t.get(original_name, ''), keyword)))
                max_score = max(score_list)
                if max_score > 0.85:
                    max_indices = [i for i, score in enumerate(score_list) if score == max_score]
                    if len(max_indices) == 1:
                        tmdb_code = results[max_indices[0]]['id']
                    else:
                        recent_result = None
                        for index in max_indices:
                            t = results[index]
                            try:
                                tmdb_year = int(t['first_air_date'].split('-')[0]) if is_show else int(t['release_date'].split('-')[0])
                            except:
                                tmdb_year = 1900
                            if recent_result is None or tmdb_year > recent_result[1]:
                                recent_result = (t['id'], tmdb_year)
                        tmdb_code = recent_result[0]
                else:
                    tmdb_code = results[0]['id']
            else:
                results_with_similarity = []
                for t in results:
                    try:
                        tmdb_year = int(t['first_air_date'].split('-')[0]) if is_show else int(t['release_date'].split('-')[0])
                    except:
                        tmdb_year = 1900
                    similarity_score = max(cls.similar(t.get(name, ''), keyword), cls.similar(t.get(original_name, ''), keyword))
                    results_with_similarity.append((t['id'], tmdb_year, similarity_score))
                results_with_similarity.sort(key=lambda x: x[2], reverse=True)
                for tmdb_id, tmdb_year, similarity_score in results_with_similarity:
                    if similarity_score >= 0.85 and tmdb_year == int(year):
                        tmdb_code = tmdb_id
                        break

                if not tmdb_code:
                    for tmdb_id, tmdb_year, similarity_score in results_with_similarity:
                        if similarity_score >= 0.85 and abs(tmdb_year - int(year)) == 1:
                            tmdb_code = tmdb_id
                            break

                if not tmdb_code:
                    for tmdb_id, tmdb_year, similarity_score in results_with_similarity:
                        if similarity_score >= 0.85 and abs(tmdb_year - int(year)) == 2:
                            tmdb_code = tmdb_id
                            break

                if not tmdb_code:
                    tmdb_code = results[0]['id']

        elif tmdb_search['results'] == [] and SiteUtil.is_include_hangul(keyword):
            try:
                if cls.search_watch(keyword=keyword, year=year)['ret'] == 'success':
                    cls.search(keyword=keyword, year=year)
            except:
                pass

        meta_cache[cache_key] = tmdb_code
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

