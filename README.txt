# json.dump and json.load
# memory --> same
# time   --> 0m9.111s  for 903072 records

# ============= DEPENDANCIES =============== 
  - python 2.6 or more
  - marisa_trie

# ========= INSTALL =======================
virtualenv venv
source ./venv/bin/activate
pip install -r requirement.txt

# Using HoneyVault
# ============= BUILD DAWG ================
# you need to run this only if you want to use new password leaks. Default set of grammar and dictionaries are provided with the code.
# Also note, if you want to use these function make necessary changes in `honeyvault_config.py` and update the required paths
python buildPCFG.py --build-dawg
python buildPCFG.py --build-pcfg

# Encoding/Encryting
python honey_vault.py --encode vault_p.txt
python honey_vault.py --decode vault_c.txt


# ============== INSTALL LIBRARIES LOCALLY ================
# Execute the following code. remember to chagne python2.6 with the version of python you are running.

mkdir -p ~/PythonLib/lib/lib/python2.6/site-packages
export PYTHONPATH=$HOME/PythonLib/lib/python2.6/site-packages
easy_install --prefix=$HOME/PythonLib marisa_trie
easy_install --prefix=$HOME/PythonLib pip

export PATH=$HOME/PythonLib/bin/:$PATH

# Some more, 
# pip install --user package_name
# pip install --install-option="--prefix=$HOME/local" package_name
# etc.
