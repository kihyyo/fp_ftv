from support import SupportYaml
from tool import ToolUtil

from .model import ModelFPFtvItem
from .setup import *
from .task_for_download import Task


class ModuleBasic(PluginModuleBase):

    def __init__(self, P):
        super(ModuleBasic, self).__init__(P, name='basic', first_menu='setting', scheduler_desc='해외TV 파일처리 - 기본')
        self.data = {
            'data' : [],
            'is_working' : 'wait'
        }
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{self.name}_interval' : '30',
            f'{self.name}_auto_start' : 'False',
            f'{self.name}_path_source' : 'C:\\FlaskFarm\\download',
            f'{self.name}_path_target' : 'C:\\FlaskFarm\\target_test',
            f'{self.name}_path_error' : 'C:\\FlaskFarm\\error_test',
            f'{self.name}_folder_format' : '{GENRE}/{TITLE_FIRST_CHAR}/{TITLE} ({YEAR})/{SEASON}',
            f'{self.name}_path_config' : "{PATH_DATA}" + os.sep + "db" + os.sep + f"{P.package_name}_{self.name}.yaml",
            f'{self.name}_task_stop_flag' : 'False',
            f'{self.name}_dry_task_stop_flag' : 'False',
            f'{self.name}_db_delete_day' : '30',
            f'{self.name}_db_auto_delete' : 'False',
            f'{P.package_name}_item_last_list_option' : '',
            f'{self.name}_is_gds_bot' : 'False',
            f'{self.name}_use_notify' : 'False',
            f'{self.name}_delete_dupe' : 'False',
            f'{self.name}_make_show_yaml' : 'False',
            f'{self.name}_yaml_path' : '{GENRE}/{TITLE_FIRST_CHAR}/{TITLE} ({YEAR})',
            f'{self.name}_etc_genre' : '기타국가드라마',
        }
        self.web_list_model = ModelFPFtvItem
        default_route_socketio_module(self, attach='/status')


    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        if sub == 'setting':
            arg['is_include'] = F.scheduler.is_include(self.get_scheduler_name())
            arg['is_running'] = F.scheduler.is_running(self.get_scheduler_name())
            arg['config_path'] = ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config'))
        return render_template(f'{P.package_name}_{self.name}_{sub}.html', arg=arg)
        

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        if command == 'refresh':
            self.refresh_data()
        elif command == 'dry_run_start':
            def func():
                self.call_task(is_dry=True)
            th = threading.Thread(target=func, args=())
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'곧 실행됩니다.'}
        elif command == 'dry_run_stop':
            if self.data['is_working'] == 'run':
                P.ModelSetting.set(f'{self.name}_dry_task_stop_flag', 'True')
                P.ModelSetting.set(f'{self.name}_task_stop_flag', 'True')
                ret = {'ret':'success', 'msg':'잠시 후 중지됩니다.'}
            else:
                ret = {'ret':'warning', 'msg':'대기중입니다.'}
        return jsonify(ret)


    def scheduler_function(self):
        self.call_task()
    
    def call_task(self, is_dry=False):
        config = self.load_basic_config()
        self.data['data'] = []
        self.data['is_working'] = 'run'
        self.refresh_data()
        config[0]['소스 폴더'] = P.ModelSetting.get(f"{self.name}_path_source")
        config[0]['타겟 폴더'] = P.ModelSetting.get(f"{self.name}_path_target")
        config[0]['에러 폴더'] = P.ModelSetting.get(f"{self.name}_path_error")
        config[0]['타겟 폴더 구조'] = P.ModelSetting.get(f"{self.name}_folder_format")
        call_module = self.name
        if is_dry:
            call_module += '_dry'
        P.ModelSetting.set(f'{call_module}_task_stop_flag', 'False')
        if F.config['use_celery']:
            result = Task.start.apply_async((config, call_module))
            try:
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            except:
                logger.debug('CELERY on_message not process.. only get() start')
                ret = result.get()
        else:
            ret = Task.start(self, config, call_module)
        self.data['is_working'] = ret
        self.refresh_data()   

    def plugin_load(self):
        if os.path.exists(ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config'))) == False:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'file', f'config_{self.name}.yaml'), ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config')))

    #########################################################
    def load_basic_config(self):
        return SupportYaml.read_yaml(ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config')))


    def refresh_data(self, index=-1):
        if index == -1:
            self.socketio_callback('refresh_all', self.data)
        else:
            self.socketio_callback('refresh_one', self.data['data'][index])
    
    def receive_from_task(self, arg, celery=True):
        try:
            result = None
            if celery:
                if arg['status'] == 'PROGRESS':
                    result = arg['result']
            else:
                result = arg
            if result is not None:
                result['index'] = len(self.data['data'])
                self.data['data'].append(result)
                self.refresh_data(index=result['index'])
        except Exception as e: 
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
