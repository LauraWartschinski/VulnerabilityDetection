from pydriller import RepositoryMining
import sys

#collect all python code for building a corpus to train the word2vec model


repos = ["https://github.com/numpy/numpy", "https://github.com/django/django", "https://github.com/scikit-learn/scikit-learn", "https://github.com/tensorflow/tensorflow", "https://github.com/keras-team/keras","https://github.com/ansible/ansible", "https://github.com/TheAlgorithms/Python", "https://github.com/pallets/flask", "https://github.com/ytdl-org/youtube-dl", "https://github.com/pandas-dev/pandas", "https://github.com/scrapy/scrapy", "https://github.com/kennethreitz/requests", "https://github.com/home-assistant/home-assistant", "https://github.com/ageitgey/face_recognition","https://github.com/emesik/mamona","https://github.com/progrium/notify-io","https://github.com/phoenix2/phoenix","https://github.com/odoo/odoo","https://github.com/ageitgey/face_recognition","https://github.com/psf/requests","https://github.com/deepfakes/faceswap","https://github.com/XX-net/XX-Net","https://github.com/tornadoweb/tornado","https://github.com/saltstack/salt","https://github.com/matplotlib/matplotlib","https://github.com/celery/celery","https://github.com/binux/pyspider","https://github.com/miguelgrinberg/flasky","https://github.com/sqlmapproject/sqlmap","https://github.com/zulip/zulip","https://github.com/scipy/scipy","https://github.com/bokeh/bokeh","https://github.com/docker/compose","https://github.com/getsentry/sentry","https://github.com/timgrossmann/InstaPy","https://github.com/divio/django-cms","https://github.com/boto/boto"]

pythontraining = ""

for r in repos:
  print(r)
  files = []
  for commit in RepositoryMining(r).traverse_commits():
      for m in commit.modifications:
        filename = m.new_path
        
        if filename is not None:
          if ".py" in filename:
            if not filename in files:
              code = m.source_code
              if code is not None:
                pythontraining = pythontraining + "\n\n" + code
                files.append(filename)
        
          
  with open('w2v/pythontraining.txt', 'w') as outfile:
    outfile.write(pythontraining)
