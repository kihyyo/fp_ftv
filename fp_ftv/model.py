from .setup import *


class ModelFPFtvItem(ModelBase):
    P = P
    __tablename__ = 'fp_ftv_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    call_module = db.Column(db.String)
    filename_original = db.Column(db.String)
    foldername = db.Column(db.String)
    filename_pre = db.Column(db.String)
    meta_find = db.Column(db.Boolean)
    quality = db.Column(db.String)
    status = db.Column(db.String) # REMOVE_BY_PRE  MOVE_BY_PRE MOVE_BY_META 
    # MOVE_BY_FTV  MOVE_BY_NOMETA MOVE_BY_NOTV
    result_folder = db.Column(db.String)
    result_filename = db.Column(db.String)
    title = db.Column(db.String)
    title_en = db.Column(db.String)
    year = db.Column(db.String)
    genre = db.Column(db.String)
    country = db.Column(db.String)
    is_vod = db.Column(db.Boolean)
    is_dry = db.Column(db.Boolean)
    yaml = db.Column(db.String)
    yaml_path = db.Column(db.String)
    log = db.Column(db.String)

    file_subtitle_count = db.Column(db.String)
    include_kor_file_subtitle = db.Column(db.Boolean)

    resolution = db.Column(db.String)
    video_codec = db.Column(db.String)
    audio_list = db.Column(db.String)
    audio_codec = db.Column(db.String)
    audio_codec_list = db.Column(db.String)
    include_kor_audio = db.Column(db.Boolean)
    video_size = db.Column(db.Integer)
    subtitle_count = db.Column(db.Integer)
    subtitle_list = db.Column(db.String)
    include_kor_subtitle = db.Column(db.Boolean)

    def __init__(self, call_module, filename_original, foldername, is_dry):
        self.call_module = call_module
        self.filename_original = filename_original
        self.result_filename = filename_original
        self.filename_pre = filename_original
        self.foldername = foldername
        self.is_dry = is_dry
        self.created_time = datetime.now()
        self.audio_count = 0
        self.subtitle_count = 0
        self.include_kor_audio = False
        self.include_kor_subtitle = False
        self.file_subtitle_count = 0
        self.file_subtitle_include_kor = False
        self.is_hard_subtitle = False
        self.log = ''

    @classmethod
    def yaml_time(cls, yaml_path):
        with F.app.app_context():
            items = F.db.session.query(cls).filter(cls.yaml_path==yaml_path).filter(cls.yaml!='null').order_by(-cls.id)
            items = items.all()
            return items


    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query1 = cls.make_query_search(F.db.session.query(cls), search, cls.filename_original)
            #query2 = cls.make_query_search(F.db.session.query(cls), search, cls.result_folder)
            #query = query1.union(query2)
            query = query1 
            if option1 != 'all':
                query = query.filter(cls.call_module == option1)
            if option2 != 'all':
                query = query.filter(cls.status == option2)
            
            if order == 'desc':
                query = query.order_by(desc(cls.id))
            else:
                query = query.order_by(cls.id)
            return query
