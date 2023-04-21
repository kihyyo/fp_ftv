# -*- coding: utf-8 -*-
#########################################################
# python
import os, traceback

# third-party
import requests
from flask import Blueprint, request, send_file, redirect

# sjva 공용
from framework import app, path_data, check_api, py_urllib, SystemModelSetting
from framework.logger import get_logger
from framework.util import Util
from plugin import get_model_setting, Logic, default_route
from tool_base import ToolUtil
# 패키지
#########################################################


class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix=f"/{package_name}", template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    plugin_info = {
        'version' : '0.1.0.0',
        'name' : package_name,
        'category' : '',
        'icon' : '',
        'developer' : u'kihyyo',
        'description' : u'해외TV 파일처리 v2',
        'home' : f'https://github.com/kihyyo/{package_name}',
        'more' : '',
    }

    menu = {
        'main' : [package_name, u'해외TV v2'],
        'sub' : [
            ['basic', u'다운로드 파일처리'], ['yaml', u'설정파일을 사용하는 다운로드 파일처리'], ['simple', u'메타 미사용 다운로드 파일처리'], ['analysis', u'방송중 폴더 분석 & 종영 처리'], ['finish', u'종영 폴더 분석'], ['manual', u'매뉴얼'], ['log', u'로그']
        ], 
        'category' : plugin_info['category'],
        'sub2' : {
            'basic' : [
                ['setting', u'설정'], ['status', u'처리 상태']
            ],
            'yaml' : [
                ['setting', u'설정'], ['status', u'처리 상태']
            ],
            'simple' : [
                ['setting', u'설정'], ['status', u'처리 상태']
            ],
            'analysis' : [
                ['setting', u'설정'], ['status', u'분석']
            ],
            'manual' : [
                ['README.md', u'다운로드 파일처리'], ['manual/analysis.md', u'방송중 폴더'], ['manual/finish.md', u'종영 폴더']
            ]
        }
    }  

    
    ModelSetting = get_model_setting(package_name, logger)
    ModelFPFtvItem = get_model_setting(package_name, logger, table_name = 'fp_ftv_item')
    logic = None
    module_list = None
    home_module = 'basic'


def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = f"sqlite:///{os.path.join(path_data, 'db', f'{P.package_name}.db')}"
        from framework.util import Util
        ToolUtil.save_dict(P.plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
        P.module_list = []
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error(f'Exception:{e}')
        P.logger.error(traceback.format_exc())


initialize()

