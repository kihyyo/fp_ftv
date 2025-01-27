
import re
import time
import traceback
import datetime
from .setup import P
from support import SupportFile, SupportString
from support_site import SiteTmdbFtv
from .site_tmdb import tmdb
logger = P.logger

EXTENSION = 'mp4|mkv|'

REGEXS = [
    r'^(?P<name>.*?)\.([sS](?P<sno>\d+))?[eE](?P<no>\d+)\.(?P<etc>.*?)?\.?(?P<quality>\d{3,4})[p|P]\.(?P<streaming>AMZN|ATVP|NF|DSNP|HMAX|PMTP|HULU|STAN|iP)?\.?(?i)(WEB-DL|WEBRip|WEB|bluray)?\.?(?i)(?P<audio>DDPA|DDP|DD|AC3|AAC|DTS-HD|DTS|TrueHD)?(?P<channel>2.0|5.1|7.1)?\.?(?P<etc2>.*?)(\-(?P<release>.*?))?(?i)(?P<container>\.mkv|\.mp4|\.srt|\.ass)$',
    r'^(?P<name>.*?)([sS](?P<sno>\d+))[eE](?P<no>\d+)(.*?)(?i)(?P<container>\.mkv|\.mp4|\.srt|\.ass)$', 
    r'^(?P<name>.*?)\.[eE](?P<no>\d+)(\-E\d{1,4})?\.?(?P<a>.*?\.)?(?P<date>\d{6})?\.(?P<etc>.*?)((?P<quality>\d+)[p|P])?(\-?(?P<release>.*?))?(?i)(?P<container>\.mkv|\.mp4|)$'
]

class EntityFtv(object):

    def __init__(self, filename, dirname=None, meta=False, is_title=False, config=None):
        self.data = {
            'filename' : {
                'original' : filename, 
                'dirname' : dirname, 
                'is_matched' : False,
                'match_index' : -1,
                'name' : '',
                'original_name': '',
            },
            'meta' : {
                'find':False,
            },
            'process_info' : {
                'rebuild':'',
                'status':''
            }
        }
        if is_title == False:
            self.analyze(config=config)
            self.data['filename']['original_name'] = self.data['filename']['name']
            if self.data['filename']['name'] != '' and config is not None:
                rule = config.get('검색어 변경', None)
                if rule is not None:
                    self.change_name(rule)
                    self.data['filename']['name'] = self.data['filename']['name'].replace('.', ' ').strip()
        else:
            self.data['filename']['name'] = filename
            self.data['filename']['is_matched'] = True
            self.data['filename']['match_index'] = -1
            self.data['filename']['date'] = ''


        search_try = False
        if meta and self.data['filename']['is_matched']:

            if search_try == False:
                self.find_meta()

    def analyze(self, config=None):
        def get(md, field):
            if field in md and md[field] is not None:
                return md[field]
            return ''

        for idx, regex in enumerate(REGEXS):
            try:
                match = re.compile(regex).match(self.data['filename']['original'])
                if match:
                    md = match.groupdict()
                    # if md['name'][-1] == '-':
                    #     md['name'] = md['name'][:-1].strip()
                    self.data['filename']['is_matched'] = True
                    self.data['filename']['match_index'] = idx
                    self.data['filename']['name'] = get(md, 'name')
                    tmp = get(md, 'sno')
                    self.data['filename']['sno'] = int(tmp) if tmp != '' else 1
                    tmp = get(md, 'no')
                    try:
                        self.data['filename']['no'] = int(tmp) if tmp != '' else -1
                        if self.data['filename']['no'] == 0:
                            raise Exception('0')
                    except:
                        self.data['process_info']['rebuild'] += 'remove_episode'
                        self.data['filename']['no'] = -1

                    self.data['filename']['streaming'] = get(md, 'streaming')
                    self.data['filename']['quality'] = get(md, 'quality')
                    self.data['filename']['release'] = get(md, 'release')
                    self.data['filename']['container'] = get(md, 'container')
                    self.data['filename']['day_delta'] = 0
                            
                    #logger.warning(d(self.data['filename']))
                    break
                else:
                    continue
            except:
                continue
                
    
    def change_name(self, rules):
        name = self.data['filename']['name']
        for rule in rules:
            try:
                name = re.sub(rule['source'], rule['target'], name, flags=re.I).strip()
            except Exception as e: 
                logger.error(f"Exception:{e}")
                logger.error(traceback.format_exc())
        self.data['filename']['name'] = name

    def find_meta(self, keyword=False, info_cache = {}):

        if keyword == False:
            keyword = self.data['filename']['name']
            year = None
            match = re.search('\d{4}', keyword)
            if match and 1950 < int(match.group()) < datetime.date.today().year + 1:
                keyword = keyword.replace(match.group(), '').strip()
                year = match.group()
        logger.debug('검색어: %s', keyword)
        tmdb_code = ''
        if keyword in info_cache:
            if info_cache[keyword]['ret'] == 'success':
                self.data['meta']['info'] = info_cache[keyword]['data']
                self.data['meta']['find'] = True
            else:
                self.data['meta']['find'] = False
        else:
            if year == None:
                tmdb_code = tmdb.search(keyword, is_show = True)
            else:
                tmdb_code = tmdb.search(keyword, is_show = True, year)
            try:
                logger.debug('TMDB 코드: %s', tmdb_code)
                if tmdb_code != None and tmdb_code != '':
                    tmdb_code = 'FT'+str(tmdb_code)
                    tmdb_info = SiteTmdbFtv.info(tmdb_code)
                    info_cache[keyword] = tmdb_info
                    if tmdb_info['ret'] == 'success':
                        self.data['meta']['info'] = tmdb_info['data']
                        self.data['meta']['find'] = True
                else:
                    self.data['meta']['find'] = False
            except Exception as e:
                logger.error(f"Exception:{str(e)}")
                logger.error(traceback.format_exc())







