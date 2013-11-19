# ============= DEPENDANCIES =============== 
  - python 2.6 or more
  - marisa_trie

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
