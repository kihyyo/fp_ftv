import imp
import json
import os
import re
import traceback, shutil
import requests
from datetime import datetime
from support import SupportDiscord, SupportFile, SupportString, SupportYaml
from support.expand.ffprobe import SupportFfprobe
from tool import ToolNotify
from .fp_entity_ftv import EntityFtv
from support_site import SiteUtil
from .model import ModelFPFtvItem
from .setup import F, P
logger = P.logger

class Task(object):
    @staticmethod
    @F.celery.task(bind=True)
    def start(self, configs, call_module):
        P.logger.warning(f"Task.start : {call_module}")

        is_dry = True if call_module.find('_dry') != -1 else False
        for config in configs:
            source = config['소스 폴더']
            target = config['타겟 폴더']
            error = config['에러 폴더']
            if is_dry != True:
                logger.debug("smi2srt 진행중")
                PP = F.PluginManager.get_plugin_instance('subtitle_tool')
                ret = PP.SupportSmi2srt.start(source, remake=False, no_remove_smi=False, no_append_ko=False, no_change_ko_srt=False, fail_move_path=None)

            for base, dirs, files in os.walk(source):
                for idx, original_filename in enumerate(files):
                    #if idx>0:return
                    if P.ModelSetting.get_bool(f"{call_module}_task_stop_flag"):
                        P.logger.warning("사용자 중지")
                        return 'stop'
                    try:                      
                        db_item = ModelFPFtvItem(call_module, original_filename, base, is_dry)
                        filename = original_filename
                        #logger.warning(f"{idx} / {len(files)} : {filename}")
                        filename = Task.process_pre(config, db_item, is_dry)
                        if filename is None:
                            continue
                        db_item.filename_pre = filename
                        db_item.target_folder = target
                        entity = EntityFtv(filename, dirname=base, meta=True, config=config)
                        if entity.data['filename']['is_matched'] :
                            db_item.meta_find = entity.data['meta']['find']
                            db_item.meta = entity.data['meta']['info']
                            db_item.quality = entity.data['filename']['quality']
                            db_item.streaming = entity.data['filename']['streaming']
                            db_item.title = db_item.meta['title']
                            db_item.title_en = db_item.meta['originaltitle']
                            db_item.year = db_item.meta['year']
                            db_item.genre = ', '.join(db_item.meta['genre'])#str(db_item.meta['genre'])[1:-1].replace("'",'') if len(db_item.meta['genre']) > 0 else '기타'
                            db_item.country = db_item.meta['country'][0] if len(db_item.meta['country']) > 0 else '정보없음'
                            db_item.target_genre = Task.make_genre(config, db_item)
                            db_item.season_no = entity.data['filename']['sno']
                            db_item.season = 'Season '+str(db_item.season_no)
                            db_item.error = error
                            if entity.data['filename']['container'] in ['.mkv', '.mp4'] :
                                if entity.data['meta']['find']:
                                    Task.process_probe(db_item)
                                    db_item.target_season = Task.make_season(config, db_item)
                                    Task.move_file(config, entity, db_item, target, is_dry)
                                else:
                                    db_item.status = "MOVE_BY_NOMETA"
                                    db_item.result_folder = os.path.join(config['경로 설정']['no_meta'].format(error=error), entity.data['filename']['name'].replace('\.',' '), 'Season '+str(int(entity.data['filename']['sno'])))
                                    if is_dry == False:
                                        Task.dedupe_move(os.path.join(base, original_filename), db_item.result_folder, db_item.result_filename)
                            elif os.path.splitext(filename)[1] in ['.srt', '.ass'] and os.path.isfile(os.path.join(db_item.foldername, db_item.filename_original)) and entity.data['meta']['find']:
                                if Task.get_video(config, db_item, base) != True:
                                    shutil.move(os.path.join(base,db_item.filename_pre),os.path.join(config['경로 설정']['sub'],db_item.filename))
                                else:
                                    continue
                        else:
                            db_item.status = "MOVE_BY_NOTV"
                            db_item.result_folder = config['경로 설정']['no_tv'].format(error=error)
                            if is_dry == False:
                                Task.dedupe_move(os.path.join(base, original_filename), db_item.result_folder, db_item.result_filename)
                        if config.get('PLEX_MATE_SCAN') != None:
                            for plex_info in config.get('PLEX_MATE_SCAN'):
                                url = f"{plex_info['URL']}/plex_mate/api/scan/do_scan"
                                P.logger.info(f"PLEX_MATE : {url}")
                                plex_target = os.path.join(db_item.result_folder, db_item.result_filename)
                                for rule in plex_info.get('경로변경', []):
                                    plex_target = plex_target.replace(rule['소스'], rule['타겟'])
                                
                                if plex_target[0] == '/':
                                    plex_target = plex_target.replace('\\', '/')
                                else:
                                    plex_target = plex_target.replace('/', '\\')
                                data = {
                                    'callback_id': f"{P.package_name}_basic_{db_item.id}",
                                    'target': plex_target,
                                    'apikey': F.SystemModelSetting.get('apikey'),
                                    'mode': 'ADD',
                                }
                                res = requests.post(url, data=data)
                                #P.logger.info(res)
                                data = res.json()
                                P.logger.info(f"PLEX SCAN 요청 : {url} {data}")
                        
                        
                        if P.ModelSetting.get_bool("basic_use_notify"):
                            msg = f"파일: {original_filename}\n최종폴더: {db_item.result_folder}\n최종파일: {db_item.result_filename}"
                            ToolNotify.send_message(msg, message_id="fp_ftv_basic", image_url=entity.data['meta'].get('poster'))

                    except Exception as e:    
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())
                    finally:
                        if db_item != None and os.path.splitext(filename)[1] in ['.mkv', '.mp4']:
                            db_item.save()
                            if F.config['use_celery']:
                                self.update_state(state='PROGRESS', meta=db_item.as_dict())
                            else:
                                P.logic.get_module(call_module.replace('_dry', '')).receive_from_task(db_item.as_dict(), celery=False)
                        #return 'wait'
                      
                if base != source and len(os.listdir(base)) == 0 :
                    try:
                        if is_dry == False:
                            os.rmdir(base)
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())

            for base, dirs, files in os.walk(source):
                if base != source and len(dirs) == 0 and len(files) == 0:
                    try:
                        if is_dry == False:
                            os.rmdir(base)
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())
            

        P.logger.debug(f"task {call_module} 종료")
        return 'wait'


    def process_pre(config, db_item, is_dry):
        filename = db_item.filename_original
        if '전처리' not in config:
            return filename

        for key, value in config['전처리'].items():
            if key == '변환':
                if value is None:
                    continue
                for rule in value:
                    try:
                        filename = re.sub(rule['source'], rule['target'], filename).strip()
                    except Exception as e: 
                            P.logger.error(f"Exception:{e}")
                            P.logger.error(traceback.format_exc())

            elif key == '파일삭제':
                if value is None:
                    continue
                for regex in value:
                    try:
                        if re.search(regex, filename):
                            try:
                                db_item.status = 'REMOVE_BY_PRE'
                                if is_dry == False:
                                    os.remove(os.path.join(db_item.foldername, db_item.filename_original))
                            except Exception as e: 
                                P.logger.error(f"Exception:{e}")
                                P.logger.error(traceback.format_exc())
                            finally:
                                return
                    except Exception as e: 
                            P.logger.error(f"Exception:{e}")
                            P.logger.error(traceback.format_exc())

            elif key == '폴더삭제':
                if value is None:
                    continue
                for rule in value:
                    try:
                        if rule in db_item.foldername:
                            try:
                                shutil.rmtree(db_item.foldername)
                            except Exception as e: 
                                    P.logger.error(f"Exception:{e}")
                                    P.logger.error(traceback.format_exc())
                            finally:
                                return
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())

            elif key == '이동':
                if value is None:
                    continue
                for target, regex_list in value.items():
                    for regex in regex_list:
                        try:
                            if re.search(regex, filename):
                                if target[0] == '/' or target[1] == ':': # 절대경로
                                    target_folder = target
                                else:
                                    if target in config['경로 설정']:
                                        target_folder = config['경로 설정'][target].format(error=config['에러 폴더'])
                                    else:
                                        target_folder = os.path.join(config['에러 폴더'], target)
                                db_item.result_folder = target
                                db_item.result_filename = db_item.filename_original
                                db_item.status = "MOVE_BY_PRE"
                                if is_dry == False:
                                    Task.dedupe_move(os.path.join(db_item.foldername, db_item.filename_original), target_folder, db_item.filename_original)
                                return
                        except Exception as e: 
                                P.logger.error(f"Exception:{e}")
                                P.logger.error(traceback.format_exc())
        return filename

    def manual_target(config, db_item):
        program_folder = None
        manual_list = config.get('타겟 수동 설정')
        if manual_list != None:
            for condition_name in manual_list:
                try:
                    mod = imp.new_module('my_code')
                    exec(condition_name['코드'], mod.__dict__)
                    if mod.check(db_item):
                        program_folder = os.path.join(condition_name['타겟루트'], condition_name['타겟포맷'].format(**Task.get_folder_folder(db_item)))
                        return program_folde
                    else:
                        continue
                except Exception as e: 
                    P.logger.error(f'Exception:{str(e)}')
                    P.logger.error(traceback.format_exc())

       


    def make_season(config, db_item):
        season = None
        season_no = int(db_item.season_no)
        season_list = config.get('시즌 설정')
        if season_list != None:
            for condition_name in season_list:
                try:
                    mod = imp.new_module('my_code')
                    exec(condition_name['코드'], mod.__dict__)
                    if mod.check(db_item):
                        season = 'Season '+str(season_no+int(condition_name['시즌번호']))+' '+'시즌 '+str(season_no)+' '+condition_name['시즌이름']
                    else:
                        continue
                except Exception as e: 
                    P.logger.error(f'Exception:{str(e)}')
                    P.logger.error(traceback.format_exc())

                if season != None:
                    break
        if season == None:
            season = 'Season '+str(season_no)
        return season
            
    def make_genre(config, db_item):
        genre = None
        genres = config['장르 변경 규칙']
        for g in genres:
            if g in db_item.genre:
                genre = config['장르 변경 규칙'].get(g,g)
            if genre != None:
                break
        if genre == None:
            for c in genres:
                if c == db_item.country:
                    genre = config['장르 변경 규칙'].get(c,c)
                if genre != None:
                    break
        if genre == None:
            genre = P.ModelSetting.get('basic_etc_genre')
        return genre
    
    def check_subtitle_file(db_item):
        source_path = os.path.join(db_item.foldername, db_item.filename_original)
        tmp = os.path.splitext(source_path)
        subtitle_list = []
        for ext in ['.ko.srt', '.kor.srt', '.ass', '.ko.ass', 'kor.ass', '.smi', '.srt', ]:
            _ = os.path.join(tmp[0] + ext)
            if os.path.exists(_):
                subtitle_list.append(_)
            else:
                continue
        return subtitle_list
    

    def move_file(config, entity, db_item, target_folder, is_dry):
        source_path = os.path.join(db_item.foldername, db_item.filename_original)
        default_folder_folder = Task.get_folder_folder(db_item)
        if True:
            year_tmp = entity.data['meta']['info']['year']
            if year_tmp == 0 or year_tmp == '0':
                year_tmp = ''
            if Task.manual_target(config, db_item) != None:
                db_item.manual_target = True
                program_folder = Task.manual_target(config, db_item)[0]
            else:
                db_item.manual_target = False
                program_folder = config['타겟 폴더 구조'].format(**default_folder_folder)
            tmps = program_folder.replace('(1900)', '').replace('()', '').replace('[]', '').strip()
            tmps = re.sub("\s{2,}", ' ', tmps) 
            tmps = re.sub("/{2,}", '/', tmps) 
            tmps = tmps.split('/')
            program_folder = os.path.join(target_folder, *tmps)
            target_filename = entity.data['filename']['original']
            if target_filename is not None:
                if is_dry == False:
                    if config['hard_subtitle'] != None:
                        for vod in config['hard_subtitle']:
                            if vod.lower() in db_item.filename_original.lower():
                                db_item.is_vod = True 
                            else:
                                db_item.is_vod = False
                    if db_item.include_kor_subtitle != True and db_item.is_vod != True:
                        subtitle_list = Task.check_subtitle_file(db_item)
                        if len(subtitle_list) > 0:
                            db_item.file_subtitle_count = len(subtitle_list)
                            db_item.include_kor_file_subtitle = True
                        else:
                            db_item.include_kor_file_subtitle = False
                    if db_item.include_kor_file_subtitle == True or db_item.include_kor_subtitle == True or db_item.is_vod == True or db_item.include_kor_audio == True :
                        db_item.result_folder = program_folder
                        db_item.result_filename = target_filename
                        db_item.status = "MOVE_BY_META"
                        if db_item.include_kor_file_subtitle == True :
                            for source_subtitle in subtitle_list:
                                Task.dedupe_move(source_subtitle, program_folder, os.path.basename(source_subtitle))
                        Task.dedupe_move(source_path, program_folder, target_filename)
                        if P.ModelSetting.get_bool('basic_make_show_yaml'):
                            Task.get_yaml(db_item)

                    else:
                        sub_x_folder = config['경로 설정']['sub_x'].format(**default_folder_folder)
                        db_item.result_folder = sub_x_folder
                        db_item.result_filename = target_filename
                        db_item.status = "MOVE_SUB_X"
                        Task.dedupe_move(source_path, sub_x_folder, target_filename)
                        
            else:
                P.logger.error(f"타겟 파일 None")


    def get_folder_folder(db_item):
        data = {}
        data['TITLE'] = SupportFile.text_for_filename(db_item.title)
        data['TITLE_EN'] = SupportFile.text_for_filename(db_item.title_en) if db_item.title_en != None else ''
        data['TITLE_FIRST_CHAR'] = SupportString.get_cate_char_by_first(db_item.title)
        data['TITLE_ALL_FIRST_CHAR'] = Task.title_all_first_char(db_item.title)
        data['YEAR'] = db_item.year
        data['GENRE'] = db_item.target_genre
        data['season'] = db_item.season
        data['SEASON'] = db_item.target_season
        data['COUNTRY'] = db_item.country
        data['QUALITY'] = db_item.quality
        data['RESOLUTION'] = db_item.resolution
        data['VIDEO_CODEC'] = db_item.video_codec
        data['AUDIO_CODEC'] = db_item.audio_codec
        data['AUDIO_COUNT'] = db_item.audio_count
        data['INCLUDE_KOR_AUDIO'] = "K" if db_item.include_kor_audio else ""
        data['SUBTITLE_COUNT'] = db_item.subtitle_count
        data['INCLUDE_KOR_SUBTITLE'] = "K" if db_item.include_kor_subtitle else ""
        data['FILE_SUBTITLE_COUNT'] = db_item.file_subtitle_count
        data['error'] = db_item.error
        return data
    
    def title_all_first_char(text):
        value = ord(text[0].upper())
        ret = '' 
        if SupportString.is_include_hangul(text[0]) :     
            if value <= ord('Z'): ret = '[0-9]'
            elif value >= ord('가') and value < ord('나'): ret += '가'
            elif value < ord('다'): ret += '나'
            elif value < ord('라'): ret += '다'
            elif value < ord('마'): ret += '라'
            elif value < ord('바'): ret += '마'
            elif value < ord('사'): ret += '바'
            elif value < ord('아'): ret += '사'
            elif value < ord('자'): ret += '아'
            elif value < ord('차'): ret += '자'
            elif value < ord('카'): ret += '차'
            elif value < ord('타'): ret += '카'
            elif value < ord('파'): ret += '타'
            elif value < ord('하'): ret += '파'
            elif value <= ord('힣'): ret += '하'
            else: ret += '[0-Z]'
        else:    
            if value >= ord('A') and value <= ord('Z'): ret += text[0].upper()
            else: ret += '[0-9]'
        return ret 

    def get_yaml_data(db_item, code=None):
        from make_yaml import get_code
        from make_yaml import yaml_utils
        try:
            if code == None:
                yaml_data = get_code.OTTCODE(db_item.title, db_item.year)
                streaming_site_list = yaml_data.get_ott_code()
                streaming_site = db_item.streaming
                user_order = None
                if db_item.include_kor_file_subtitle == True :
                    user_order = ['TVING', 'WAVVE', 'COUPANG']
                elif streaming_site != '':
                    for site in ['NF', 'DSNP', 'ATVP', 'AMZN']:
                        if site == streaming_site:
                            user_order = [site]
                else:
                    user_order = ['NF', 'DSNP', 'ATVP', 'AMZN']
                if user_order != None and streaming_site_list != []:
                    code = yaml_utils.YAMLUTILS.code_sort(user_order, streaming_site_list)
                    logger.debug(code)
            if code != None:
                show_data = yaml_utils.YAMLUTILS.get_data(code)
                if len(show_data) > 0:
                    return show_data
                else:
                    return
            else:
                return
        except Exception as e: 
            P.logger.error(f"Exception:{e}")
            P.logger.error(traceback.format_exc())

        
    def get_yaml(db_item):
        if db_item.manual_target == True:
            yaml_path = db_item.yaml_path
        else:
            yaml_path = os.path.join(db_item.target_folder, P.ModelSetting.get('basic_yaml_path').format(**Task.get_folder_folder(db_item)))
        items = ModelFPFtvItem.yaml_time(yaml_path)
        db_item.yaml_path = yaml_path
        if not os.path.exists(os.path.join(yaml_path, 'show.yaml')):
            if len(items) > 0:
                return
            else:
                if Task.get_yaml_data(db_item) != None:
                    show_data = Task.get_yaml_data(db_item)
                    SupportYaml.write_yaml(os.path.join(yaml_path, 'show.yaml'), show_data)
                    db_item.yaml = "yaml_success"
                else:
                    db_item.yaml = "yaml_fail"
        else:
            if len(items) > 0:
                item = items[0]
                if item.yaml == "yaml_pass" or item.yaml == "yaml_fail" :
                    return
                else:
                    given_time = item.created_time
                    current_time = datetime.now()
                    time_diff = current_time - given_time
                    time_diff_seconds = time_diff.total_seconds()
                    logger.debug(time_diff_seconds)
                    if time_diff_seconds < 64800 :
                        return
                    else:
                        yaml_code = SupportYaml.read_yaml(os.path.join(yaml_path, 'show.yaml'))['code']
                        show_data = Task.get_yaml_data(db_item, yaml_code)
                        SupportYaml.write_yaml(os.path.join(yaml_path, 'show.yaml'), show_data)
                        db_item.yaml = "yaml_success"
            elif SupportYaml.read_yaml(os.path.join(yaml_path, 'show.yaml'))['primary'] != False:
                db_item.yaml = "yaml_pass"
            else:
                try:
                    yaml_code = SupportYaml.read_yaml(os.path.join(yaml_path, 'show.yaml'))['code']
                    show_data = Task.get_yaml_data(db_item, yaml_code)
                    if show_data != None or show_data != []:
                        SupportYaml.write_yaml(os.path.join(yaml_path, 'show.yaml'), show_data)
                        db_item.yaml = "yaml_success"
                    else:
                        db_item.yaml = "yaml_fail"
                except:
                    db_item.yaml = "yaml_fail"
                    return


    def dedupe_move(source_path, target_dir, target_filename):
        if P.ModelSetting.get_bool('basic_delete_dupe'):
            try:
                if os.path.exists(target_dir) == False:
                    os.makedirs(target_dir)
                target_path = os.path.join(target_dir, target_filename)
                if source_path != target_path:
                    if os.path.exists(target_path):
                        if os.path.getsize(source_path) == os.path.getsize(target_path):
                            os.remove(source_path)
                        else:
                            os.remove(target_path)
                            shutil.move(source_path, target_path)
            except Exception as e:
                logger.debug(f"Exception:{str(e)}")
                logger.debug(traceback.format_exc())
        else:
            SupportFile.file_move(source_path, target_dir, target_filename)


    def process_probe(db_item):
        db_item.ffprobe = SupportFfprobe.ffprobe(os.path.join(db_item.foldername, db_item.filename_original))
        if 'format' not in db_item.ffprobe:
            return False
        db_item.video_size = int(db_item.ffprobe['format']['size'])
        vc = 0
        audio_codec_list = []
        subtitle_list = []
        for track in db_item.ffprobe['streams']:
            if track['codec_type'] == 'video':
                vc += 1
                if db_item.video_codec is None:
                    db_item.video_codec = track['codec_name'].upper()
                    db_item.resolution = f"{track['coded_width']}x{track['coded_height']}"
            elif track['codec_type'] == 'audio':
                db_item.audio_count += 1
                if 'tags' in track and 'language' in track['tags']:
                    db_item.audio_list = track['tags']['language']
                    #P.logger.info(track['tags']['language'])
                    if track['tags']['language'] in ['kor', 'ko']:
                        db_item.include_kor_audio = True
                
                tmp = track['codec_name'].upper()
                if db_item.audio_codec is None:
                    db_item.audio_codec = tmp
                if tmp not in audio_codec_list:
                    audio_codec_list.append(tmp)

            elif track['codec_type'] == 'subtitle':
                db_item.subtitle_count += 1
                if 'tags' in track and 'language' in track['tags']:
                    #P.logger.info(track['tags']['language'])
                    if track['tags']['language'] in ['kor', 'ko']:
                        db_item.include_kor_subtitle = True
                    if track['tags']['language'] not in subtitle_list:
                        subtitle_list.append(track['tags']['language'])
            elif track['codec_type'] in ['data', 'attachment']:
                P.logger.debug("코덱 타입이 데이타")
            else:
                P.logger.debug("코덱 타입이 없음")
        db_item.audio_codec_list = ', '.join(audio_codec_list)
        db_item.subtitle_list = ', '.join(subtitle_list)
        #P.logger.debug(f"VC : {vc}")
        return True
    

    def get_video(config, db_item, base):
        try:
            match = re.search(r'(?i)(.ko.srt|.kor.srt|.kor.ass|.ko.ass|.ass)$', db_item.filename_pre)
            tmp = db_item.filename_pre.replace(match.group(),'').strip()
            for ext in ['.mkv', '.mp4']:
                _ = os.path.join(tmp + ext)
                if not os.path.isfile(os.path.join(db_item.foldername, _)):
                    logger.debug("자막에 맞는 동영상 파일 불러오는 중")
                    target_folder = config['경로 설정']['sub_x'].format(**Task.get_folder_folder(db_item))
                    if os.path.isdir(target_folder):
                        file_list = os.listdir(target_folder)
                        if os.path.join(tmp + ext) in file_list:
                            shutil.move(os.path.join(target_folder, _), os.path.join(base, _))
                            logger.debug("불러오기 성공. 다음 탐색시 이동")
                            return True
                        else:
                            continue    
                    else:
                        logger.debug("자막에 맞는 sub_x 폴더 없음")
                        return False   
                else:
                    return True

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())                    
                
