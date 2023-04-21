
import re
import time
import traceback
from datetime import datetime
from .setup import P
from support import SupportFile, SupportString
from support_site import SiteTmdbFtv

logger = P.logger

EXTENSION = 'mp4|avi|mkv|ts|wmv|m2ts|smi|srt|ass|m4v|flv|asf|mpg|ogm'

REGEXS = [
    r'^(?P<name>.*?)\.([sS](?P<sno>\d+))?[eE](?P<no>\d+)\.(?P<etc>.*?)?\.?(?P<quality>\d{3,4})[p|P]\.(?P<streaming>AMZN|ATVP|NF|DSNP|HMAX|PMTP|HULU|STAN|iP)?\.?(?i)(WEB-DL|WEBRip|WEB|bluray)?\.?(?i)(?P<audio>DDPA|DDP|DD|AC3|AAC|DTS-HD|DTS|TrueHD)?(?P<channel>2.0|5.1|7.1)?\.?(?P<etc2>.*?)(\-(?P<release>.*?))?(?i)(?P<container>\.mkv|\.mp4|\.avi|\.flv|\.wmv|\.ts)$',
    r'^(?P<name>.*?)([sS](?P<sno>\d+))?[eE](?P<no>\d+)(.*?)(?i)(?P<container>\.mkv|\.mp4|\.avi|\.flv|\.wmv|\.ts)$', 
    r'^(?P<name>.*?)\.([sS](?P<sno>\d+))?[eE](?P<no>\d+)(\-E\d{1,4})?\.?(?P<a>.*?\.)?(?P<date>\d{6})\.(?P<etc>.*?)((?P<quality>\d+)[p|P])?(\-?(?P<release>.*?))?(\.(.*?))?$'
]

#합본처리 제외
#_REGEX_FILENAME_RENAME = r'(?P<title>.*?)[\s\.]E?(?P<no>\d{1,2})[\-\~\s\.]?E?\d{1,2}'

class EntityFtv(object):
    meta_cache = {}
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
            match = re.compile(regex).match(self.data['filename']['original'])
            if not match:
                continue
            md = match.groupdict()
            if md['name'][-1] == '-':
                md['name'] = md['name'][:-1].strip()
            self.data['filename']['is_matched'] = True
            self.data['filename']['match_index'] = idx
            self.data['filename']['name'] = get(md, 'name').replace('.', ' ').strip()
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
                
    
    def change_name(self, rules):
        name = self.data['filename']['name']
        for rule in rules:
            try:
                name = re.sub(rule['source'], rule['target'], name, flags=re.I).strip()
            except Exception as e: 
                logger.error(f"Exception:{e}")
                logger.error(traceback.format_exc())
        self.data['filename']['name'] = name


    def find_meta(self):
        from .site_tmdb import tmdb
        tmdb_code = tmdb.search(self.data['filename']['name'])
        try:
            if tmdb_code != '':
                tmdb_code = 'FT'+str(tmdb_code)
                if SiteTmdbFtv.info(tmdb_code)['ret'] == 'success':
                    self.data['meta']['info'] = SiteTmdbFtv.info(tmdb_code)['data']
                    self.data['meta']['find'] = True

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())


