
function make_one(data) {
  row = j_row_start_hover();
  row += make_log("경로", data.foldername);
  row += make_log("파일명", data.filename_original);

  if (data.status == 'REMOVE_BY_PRE') {
    row += make_log('전처리', color("전처리로 삭제"));
  } else if (data.status == 'MOVE_BY_PRE') {
    row += make_log('전처리', color("전처리로 이동"));
  }
  
  if (data.filename_original != data.filename_pre) {
    row += make_log("전처리 후 파일명", color(data.filename_pre));
  }

  if (data.filename_pre != null) {
    if (data.entity_data.filename.is_matched) {
        tmp = data.entity_data.filename.original_name;
      if (data.entity_data.filename.original_name != data.entity_data.filename.name) {
        tmp += ' / 검색용 : ' + color(data.entity_data.filename.name, 'blue');
      }
      tmp += ' / 회차 : ' + data.entity_data.filename.no;
      tmp += ' / 날짜 : ' + data.entity_data.filename.date;
      tmp += ' / 화질 : ' + data.entity_data.filename.quality;
      tmp += ' / 릴 : ' + data.entity_data.filename.release;
      tmp += ' / ETC : ' + data.entity_data.filename.etc;
      tmp += ' / MORE : ' + data.entity_data.filename.more;
      row += make_log('파일명에서 추출한 정보', tmp);

      tmp = (data.entity_data.meta.find) ? "매칭" : '<span style="color:red; font-weight:bold">메타 찾지 못함</span>';
      row += make_log('<span style="font-weight:bold">메타 매칭</span>', tmp);
      if (data.entity_data.meta.find) {
        row += make_log("방송", data.entity_data.meta.info.title + ' (' + data.entity_data.meta.info.year + ')' + ' / ' + data.entity_data.meta.info.code + ' / ' + data.entity_data.meta.info.genre[0] );
        if ( data.entity_data.process_info.episode != null) {
          tmp = JSON.stringify(data.entity_data.process_info.episode, null, 4);
          row += make_log("해당 에피소드 정보", '<pre>' + tmp + '</pre>');

        }
      }
    } else {
      row += make_log('파일명', color('TV 파일 형식이 아님'));
    }

    tmp = data.entity_data.process_info.status;
    if (tmp != '') {
      if (data.entity_data.process_info.rebuild != '') {
        tmp += ' / ' + data.entity_data.process_info.rebuild;
      }
      row += make_log("처리 요약", tmp);
    }
  
  
    row += make_log("최종 경로", data.result_folder);
    if (data.filename_original == data.result_filename) {
      tmp = '<span style="color:blue; font-weight:bold">' + data.result_filename + '</span>' 
    } else {
      tmp = '<span style="color:red; font-weight:bold">' + data.result_filename + '</span>';
    }
    row += make_log("최종 파일명", tmp);
  }
  row += j_row_end();
  return row
}
