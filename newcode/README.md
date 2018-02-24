## New code for NoCrack [![Build Status](https://travis-ci.org/rchatterjee/nocrack.svg?branch=master)](https://travis-ci.org/rchatterjee/nocrack)


## Code structure. 
Coming soon.

## Dependencies  
Upgraded the project to Python 3.4.x. You can install it using [`pyenv`](https://github.com/pyenv/pyenv).
<!-- Tips: for using `json` in python 2.6, try installing 'simplejson'. (I.e., `$ pip install simplejson`) -->
  - python-dev (e.g., `$ sudo apt-get install python-dev` in Debian machine)
  - Others are given in the `requirement.txt`.


### Install dependencies  
Use `virtualenv` to checkout the code. It has lots of dependencies, so
virtualenv will be useful. <!-- Download the package from -->
<!-- https://pypi.python.org/pypi/virtualenv/#downloads, unpack and run  -->
<!-- `python virtualenv-x.xx/virtualenv.py venv` inside `nocrack` directory.   -->
<!-- If you have virtualenv installed then run `virtualenv venv` -->

```bash
$ virtualenv -py3 ./venv # or 
$ python3 -m venv ./venv

$ source ./venv/bin/activate 
$ pip install -r requirement.txt 
``` 

Now you shouold have all the required libraries to run `nocrack`.

## Building the PCFG (for new password leak)  
The gramar (`static/gramar.cfg.gzip`) can be rebuilt using any password leak data (password, frequency info).
Password leak files can be found [here](https://wiki.skullsecurity.org/Passwords). 
```bash
$ python buildPCFG.py --buildG rockyou-withcount.txt.bz2 --parallel
```

This will take a while depending on the size of the password leak file.
See `python buildPCFG.py --help` for more info. It will replace the grammar file in `static/grammar.cfg.gzip`. 


<!-- ## Building the PCFG for new password leak -->
<!--   For fast access of all the passwords, in the grammar, I used directed acyclic word graph (DAWG) datastructure. This is similar -->
<!--   to prefix trie with some performance improvements. The grammer using RockYou password leak is already included. If you want to train -->
<!--   a grammar (probabilities in the grammar) on different password leak, please run the following command. The paths for the leak files -->
<!--   are now hard-coded (I know this is a bad design!), so you have to make changes in `honeyvault_config.py` file with the required paths. -->

<!-- ```bash -->
<!-- $ python buildPCFG.py --build-dawg -->
<!-- $ python buildPCFG.py --build-pcfg -->
<!-- ``` -->
<!-- Or -->
<!-- ```bash -->
<!-- $ python buildPCFG.py --build-all               # Alias over the above commands. Preferable :P.  -->
<!-- ``` -->

## How to run?

**Dont forget to activate your virtualvenv and navigate to `nocrack/newcode/` directory.** 
All code is to be run from that directory.
```bash
$ source venv/bin/activate
(venv) $
``` 

The main command interface for nocrack is the `hone_client.py` file. 
It takes several options, explained one by one below.

```bash
(venv) $ ./honey_client [OPTION] [parameters]

(venv) $ ./honey_client
-getpass - <function get_pass at 0x1aad0c8>
-import - <function import_vault at 0x1aad140>
-refresh - <function refresh at 0x1aa8ed8>
-genpass - <function gen_pass at 0x1aad230>
-read - <function read at 0x1aa8e60>
-getdomainhash - <function get_static_domains at 0x1aa8f50>
-register - <function register at 0x1aa8cf8>
-write - <function write at 0x1aa8de8>
-addpass - <function add_pass at 0x1aad050>
-export - <function export_vault at 0x1aad1b8>
-default - <function default at 0x1aad2a8>
-verify - <function verify at 0x1aa8d70>
```


NoCrack server simulates the functionality of NoCrack to sync with a server, so that
one can access their password vault from all other machines. The server will run locally
in this demo case. However, you can try to running the server in remote machine and 
udpate the URL in `honeyvault_config.py` file (replacing `http://localhost:5000`).
>> TODO: Add HTTPS

To run the nocrack server run, 
```bash
(venv) $ pwd
/tmp/nocrack/newcode
(venv) $ python -V
Python 3.6.2
(venv) $ python -m server.honey_server
```

(a) __Add Password__ 
```bash
(venv) $ ./honey_client -addpass

cmd: add password
(venv) $ server/honey_client.py -addpass <master-password> <domain> <password>
e.g. (venv) $ server/honey_client.py -addpass AwesomeS@la google.com 'FckingAwesome!'
```

(b) __Get your stored password__
```bash
(venv) $ ./honey_client -getpass <master-password> <domain>
```

(c) __Genrate Random password__
  Remember this also stores the password in the vault. (Careful it might overwrite your old 
  password for that domain.)
  ```bash
  (venv) $ ./honey_client -genpass <master-password> <domain>
  ```

(d) __Upload the vault to the Storage service__
  The `vault-file` is in <base-dir>/static/vault.db, `token` is what you have got while you verify your indentity in
  the server. See `-verify` commnad bellow.
  If you haven't registered for an account in the server (or you dont remember), follow the registration steps.
  ```bash
  (venv) $ ./honey_client -write <email> <token> <vault-file>
  ```

(e) __Retrieve vault form the server__
  _Warning! it will overwrite the static/vault.db_
  ```bash
  (venv) $ ./honey_client -write <email> <token>
  ```
  
(f) __Register and verify an account at the server__
  To upload the encrypted vault you have to use a `beraer-token`, that verifies that you are the genuine owner of the
  account. The steps of obtaining the `bearer-token` is as follows: first, if you haven't registered your account or
  forgot the `verifier-token`, obtain it back by running `-register` command with an email address. (If you forgot 
  you `verifier-tokne` and want to recover the account, please use the same email address as used before.) On registration
  the server will send an random token, we call `verifier-token`, to the registered email address. This will verify taht
  you are the genuine owner of the email address. Using the `verifier-token` you can obtain a what we call `bearer-token` using
  `-verify` command.  For all subsequent communication to the server has to be authenticated using this `bearer-token`.
  So, please keep it safe and secure. May be in some online store.
  
  ```bash 
  (venv) $ ./honey_client -register <email>
  (venv) $ ./honey_client -verify <email> <token>
  ```
  You can obviously refresh `beaere-token` if need be. 

(g) __Refresh bearer token__
  If you find that your token is leaked to the adversary, you can revoke the access to the token using `-refresh` command.
  You will need the old token to perform the revoke operation. If the adversary has already chagned your token. 
  You have to go through the registration process again to regain access to your stored vault. 
  Note, the adversary might have obtained the nocrack vault, but it is still honeyencrypted and not possible to break
  without communicating with the server. So don't start changing passwords for the websites right away, take time and change
  all of them in one go, plus change your master password as well. 
  ```bash
  (venv) $ ./honey_client -refresh <email> <token>
  ```

(h) __Get statically-mapped domain hash__
  Using this command you can update your `static/static_domain_hashes.txt` file 
  ```bash
  (venv) $ ./honey_client -getdomainhash <email> <token> > static/static_domain_hashses.txt
  ```

Note, `-import` and `-export` commands are not implemented yet!



## Breaking password into chunks.
You can use the `pcfg/pcfg.py` to break passwords into chunks. 
```bash
[nocrack/newcode] $ python -m pcfg.pcfg -ptree "Password@123"
Parse Tree for Password@23
[('G', 'W7,W1,D2'), ('W7', 'password'), ('L', 'Caps'), ('W1', 'a'), ('L', 'l33t'), ('L_a', '@'), ('D2', '23')]
Size: 7
```

You can also look at [zxcvbn-python](https://github.com/dwolfhub/zxcvbn-python)
for a simpler parsing into chunks. They don't have an public API, so you have to
dig the code little bit. 





## A HoneyVault (personal note)
There are three different PCFG floating around.
1. A password-PCFG, to sample password from this pcfg
   - Need procedure to
   a. train this grammar
   b. sample from this grammar, and get the parse tree (with probs)

2. A vault-PCFG, to sample vault distribution. 
   - same as pasword-PCFG
   
3. A sub-grammar (that is just like password-PCFG but subsampled from the original one) 



