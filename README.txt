# DEPENDANCIES
  - python 2.7.x or more  (http://stackoverflow.com/a/5507373/1792013)
  - python-dev
  - (check requirement.txt)

# ========= INSTALL =======================
# To install virtualenv, just download from https://pypi.python.org/pypi/virtualenv/#downloads
# unpack and run 'python virtualenv-x.xx/virtualenv.py venv'  
$ virtualenv venv
$ source ./venv/bin/activate
$ pip install -r requirement.txt 
$ git clone -b vault1.1 git@bitbucket.org:rchatterjee/honeyencryption.git


# ============= BUILD DAWG ================
# you need to run this only if you want to use new password leaks. Default set of grammar and dictionaries are provided with the code.
# Also note, if you want to use these function make necessary changes in `honeyvault_config.py` and update the required paths
$ python buildPCFG.py --build-dawg
$ python buildPCFG.py --build-pcfg
$ python buildPCFG.py --build-all               # preferable :P

# ============= Honey ENCODING/ENCRYTING ==========
$ ./honey_client
(Follow the options provided by this)
# to start the server run - 
$ python server/honey_server.py

(For more details check honey_client_doc.txt)


------------------------------------ END ---------------------------------
# ======== These are all old versions. Just for information =======
python honey_vault.py --encode vault_p.txt
python honey_vault.py --decode vault_c.txt


# ============== INSTALL LIBRARIES LOCALLY ================
# Execute the following code. remember to chagne python2.6 with the version of python you are running.
# ** Not required if you are using venv!  **
mkdir -p ~/PythonLib/lib/lib/python2.6/site-packages
export PYTHONPATH=$HOME/PythonLib/lib/python2.6/site-packages
easy_install --prefix=$HOME/PythonLib marisa_trie
easy_install --prefix=$HOME/PythonLib pip

export PATH=$HOME/PythonLib/bin/:$PATH

# Some more, 
# pip install --user package_name
# pip install --install-option="--prefix=$HOME/local" package_name
# etc.
# json.dump and json.load
# memory --> same
# time   --> 0m9.111s  for 903072 records
