import requests
from flask import Flask, render_template, request
import json
from dataclasses import dataclass
import os


@dataclass
class BilibiliVideo:
    aid: str
    typename: str
    title: str
    description: str
    author: str
    duration: str
    is_vocaloid: bool
    on_vdb: bool = False
    vdb_id: str = ''


app = Flask(__name__)


@app.route('/')
def render_videos():
    non_vocaloid = request.cookies.get('non_vocaloid')
    if non_vocaloid is None:
        non_vocaloid = True
    else:
        non_vocaloid = True if non_vocaloid == 'True' else False
    keyword = request.args.get('keyword')
    if keyword is not None:
        with_page = request.cookies.get('on_vdb')
        if with_page is None:
            with_page = True
        else:
            with_page = True if with_page == 'True' else False
        page = request.args.get('page')
        if page is None:
            page = 1
        else:
            page = int(page)

        response = json.loads(requests.get(
            f'https://api.bilibili.com/x/web-interface/search/all/v2?context=&page={page}&order=&keyword={keyword}').text)
        pages = int(response['data']['pageinfo']['video']['pages'])
        video_list = response['data']['result'][8]['data']

        parsed_videos = []
        for video in video_list:
            mins, secs = video['duration'].split(':')
            parsed_videos.append(BilibiliVideo(video['id'], video['typename'],
                                               video['title'].replace('<em class="keyword">', '').replace('</em>', ''),
                                               video['description'], video['author'],
                                               mins + ':' + (secs if len(secs) > 1 else f'0{secs}'),
                                               video['typename'] == 'VOCALOID·UTAU'))

        for i, _ in enumerate(parsed_videos):
            response = json.loads(
                requests.get(f'https://vocadb.net/api/songs/byPv?pvService=Bilibili&pvId={parsed_videos[i].aid}').text)
            if response is not None:
                parsed_videos[i].on_vdb = True
                parsed_videos[i].vdb_id = response['id']

        page_range_start = page - 5 if page - 5 > 0 else 1
        page_range_end = min(10, pages) if page_range_start == 1 else min(page + 5, pages)

        return render_template('index.html', videos=parsed_videos, page=page, keyword=keyword, pages=pages,
                               pg_range=list(range(page_range_start, page_range_end + 1)),
                               left_bound=page>5, right_bound=page<pages-5,
                               non_vocaloid=non_vocaloid, with_page=with_page)
    return render_template('index.html', keyword='', non_vocaloid=non_vocaloid)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
