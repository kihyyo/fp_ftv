setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': '해외TV 파일처리',
        'list': [
            {
                'uri': 'list',
                'name': '목록',
            },
            {
                'uri': 'basic',
                'name': '다운로드 파일처리',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'status', 'name': '처리 상태'},
                ]
            },
            
            {
                'uri': 'manual',
                'name': '매뉴얼',
                'list': [
                    {'uri':'README.md', 'name':'README.md'}
                ]
            },
            {
                'uri': 'log',
                'name': '로그',
            },
        ]
    },
    'setting_menu': None,
    'default_route': 'normal',
}


from plugin import *

P = create_plugin_instance(setting)

try:
    from .mod_basic import ModuleBasic
    from .mod_list import ModuleList

    P.set_module_list([ModuleList, ModuleBasic])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())

logger = P.logger


"""
{
                'uri': 'yaml',
                'name': '설정파일을 사용하는 다운로드 파일처리',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'status', 'name': '처리 상태'},
                ]
            },
            {
                'uri': 'simple',
                'name': '메타 미사용 다운로드 파일처리',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'status', 'name': '처리 상태'},
                ]
            },
            {
                'uri': 'analysis',
                'name': '방송중 폴더 분석 & 종영 처리',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'status', 'name': '분석'},
                ]
            },
"""