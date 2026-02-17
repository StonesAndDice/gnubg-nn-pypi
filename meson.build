# meson.build
project(
    'gnubg',
    ['cpp', 'c'],
    version: run_command(['src/_build_utils/_version.py'], check: true).stdout().strip(),
    meson_version : '>=1.7.0',
)

# -----------------------------------------------------------------------------
# 1. Setup Environment & Dependencies
# -----------------------------------------------------------------------------
python3 = import('python').find_installation('python3', pure: false)
python_dep = python3.dependency()
pkgdir = python3.get_install_dir()
cc = meson.get_compiler('c')

# Dependencies
glib_dep = dependency('glib-2.0')
gthread_dep = dependency('gthread-2.0')
gmodule_dep = dependency('gmodule-2.0')
math_dep = cc.find_library('m', required: false)

# Collect all deps
all_deps = [python_dep, glib_dep, gthread_dep, gmodule_dep, math_dep]

# -----------------------------------------------------------------------------
# 2. Configuration (config.h)
# -----------------------------------------------------------------------------
conf_data = configuration_data()

# --- Feature Flags ---
conf_data.set('_CRT_SECURE_NO_WARNINGS', 1)
conf_data.set('NOMINMAX', 1)
conf_data.set('LOADED_BO', 1)
conf_data.set('OS_BEAROFF_DB', 1)
conf_data.set('HAVE_CONFIG_H', 1)
conf_data.set('HAVE_GLIB', 1)
conf_data.set('USE_MULTITHREAD', 1)
conf_data.set('HAVE_UNISTD_H', 1)
conf_data.set('HAVE_SYS_TYPES_H', 1)
conf_data.set('HAVE_SYS_TIME_H', 1)

# --- Standard Autotools Definitions ---
# These are required by openurl.c and generic gnubg code
conf_data.set_quoted('PACKAGE', 'gnubg')
conf_data.set_quoted('LOCALEDIR', '/usr/share/locale') # Placeholder is fine for now

# --- Web Browser Command (for openurl.c) ---
host_system = host_machine.system()
if host_system == 'darwin'
  conf_data.set_quoted('OPEN_URL_PROG', 'open')
elif host_system == 'windows'
  conf_data.set_quoted('OPEN_URL_PROG', 'cmd /c start')
else
  conf_data.set_quoted('OPEN_URL_PROG', 'xdg-open')
endif

# --- [CRITICAL FIX] Standard Directory Paths for util.c ---
# These are required by the C code to compile.
# We set them to generic defaults. The Python runtime will likely
# override the actual lookup paths using GNUBGHOME.
conf_data.set_quoted('AC_DATADIR', '/usr/local/share')
conf_data.set_quoted('AC_PKGDATADIR', '/usr/local/share/gnubg')
conf_data.set_quoted('AC_DOCDIR', '/usr/local/share/doc/gnubg')

# --- Version & Date Strings ---
conf_data.set_quoted('VERSION', meson.project_version())

date_cmd = run_command('date', '+%Y-%m-%d', check: false)
if date_cmd.returncode() == 0
  conf_data.set_quoted('BUILD_DATE', date_cmd.stdout().strip())
else
  conf_data.set_quoted('BUILD_DATE', '2025-01-01')
endif

config_h = configure_file(
    output: 'config.h',
    configuration: conf_data
)
add_project_arguments('-include', 'config.h', language: ['c', 'cpp'])

# -----------------------------------------------------------------------------
# 3. Source Definitions
# -----------------------------------------------------------------------------

# --- A. Neural Net Sources (for gnubg.nn) ---
gnubg_inc = include_directories(
    'src/gnubg-nn',
    'src/gnubg-nn/gnubg',
    'src/gnubg-nn/gnubg/lib',
    'src/gnubg-nn/analyze',
    'src/gnubg-nn/py',
)

nn_c_sources = files(
    'src/gnubg-nn/gnubg/bearoffdb.c',
    'src/gnubg-nn/gnubg/eggmoveg.c',
    'src/gnubg-nn/gnubg/eval.c',
    'src/gnubg-nn/gnubg/inputs.c',
    'src/gnubg-nn/gnubg/mt19937int.c',
    'src/gnubg-nn/gnubg/positionid.c',
    'src/gnubg-nn/gnubg/pub_eval.c',
    'src/gnubg-nn/gnubg/lib/hash.c',
    'src/gnubg-nn/gnubg/lib/neuralnet.c',
    'src/gnubg-nn/gnubg/lib/nsse.c',
)

nn_cpp_sources = files(
    'src/gnubgmodule/gnubgmodule.cpp',
    'src/gnubg-nn/analyze/analyze.cc',
    'src/gnubg-nn/analyze/bm.cc',
    'src/gnubg-nn/analyze/bms.cc',
    'src/gnubg-nn/analyze/danalyze.cc',
    'src/gnubg-nn/analyze/dice_gen.cc',
    'src/gnubg-nn/analyze/equities.cc',
    'src/gnubg-nn/analyze/mec.cc',
    'src/gnubg-nn/analyze/player.cc',
    'src/gnubg-nn/gnubg/bearoffgammon.cc',
    'src/gnubg-nn/gnubg/racebg.cc',
    'src/gnubg-nn/gnubg/osr.cc',
)

# --- B. Full Engine Sources (for gnubg) ---
gnubg_full_inc = include_directories(
    'src/gnubg',
    'src/gnubg/lib'
)

gnubg_core_sources = files(
    'src/gnubg/analysis.c',
    'src/gnubg/bearoff.c',
    'src/gnubg/bearoffgammon.c',
    'src/gnubg/boardpos.c',
    'src/gnubg/dbprovider.c',
    'src/gnubg/dice.c',
    'src/gnubg/eval.c',
    'src/gnubg/export.c',
    'src/gnubg/file.c',
    'src/gnubg/format.c',
    'src/gnubg/formatgs.c',
    'src/gnubg/glib-ext.c',
    'src/gnubg/html.c',
    'src/gnubg/import.c',
    'src/gnubg/latex.c',
    #'src/gnubg/makeweights.c',
    'src/gnubg/matchequity.c',
    'src/gnubg/matchid.c',
    'src/gnubg/mec.c',
    'src/gnubg/multithread.c',
    'src/gnubg/openurl.c',
    'src/gnubg/osr.c',
    'src/gnubg/output.c',
    'src/gnubg/positionid.c',
    'src/gnubg/progress.c',
    'src/gnubg/randomorg.c',
    'src/gnubg/relational.c',
    'src/gnubg/rollout.c',
    'src/gnubg/set.c',
    'src/gnubg/sgf.c',
    'src/gnubg/simpleboard.c',
    'src/gnubg/text.c',
    'src/gnubg/timer.c',
    'src/gnubg/util.c',
    'src/gnubg/lib/list.c',
    'src/gnubg/lib/md5.c',
)

# -----------------------------------------------------------------------------
# 4. Build Targets
# -----------------------------------------------------------------------------

# A. STATIC LIB for Neural Net
libgnubg_nn = static_library(
    'gnubg_nn_static',
    nn_c_sources + nn_cpp_sources,
    include_directories : gnubg_inc,
    cpp_args            : ['-std=c++14', '-Wno-unused-but-set-variable'],
    install             : false,
    dependencies        : all_deps,
)

gnubg_nn_dep = declare_dependency(
    include_directories : gnubg_inc,
    link_with           : libgnubg_nn,
).as_link_whole()

# B. EXTENSION: gnubg.nn (The Neural Net Module)
# Name = 'nn'. Subdir = 'gnubg'.
# Result = site-packages/gnubg/nn.so -> import gnubg.nn
py_ext_nn = python3.extension_module(
    'nn',
    [],
    dependencies : [gnubg_nn_dep, all_deps],
    install      : true,
    subdir       : 'gnubg',
)

# C. EXTENSION: gnubg._gnubg (The Full Engine Core)
# Name = '_gnubg'. Subdir = 'gnubg'.
# Result = site-packages/gnubg/_gnubg.so -> accessed by __init__.py
py_ext_full = python3.extension_module(
    '_gnubg',
    sources: gnubg_core_sources + files('src/gnubgmodule/gnubg_bridge.cpp'),
    dependencies: all_deps,
    include_directories: gnubg_full_inc,
    install: true,
    subdir: 'gnubg',
    cpp_args: ['-std=c++14', '-DGNUBG_PYTHON_EXTENSION']
)

# -----------------------------------------------------------------------------
# 5. Installs & Tests
# -----------------------------------------------------------------------------

# Version file
custom_target(
    'generate_version',
    output: '__version__.py',
    command: [python3, files('src/_build_utils/_version.py'), '--write', '@OUTPUT@'],
    build_by_default: true,
    install: true,
    install_dir: join_paths(pkgdir, 'gnubg') # Install to main pkg
)

# Install main package Init (gnubg/__init__.py)
install_data(
    'src/gnubgmodule/__init__.py',
    install_dir: join_paths(pkgdir, 'gnubg')
)

# Install Type Hints (gnubg/gnubg.pyi)
install_data(
    'src/gnubgmodule/gnubg.pyi',
    install_dir: join_paths(pkgdir, 'gnubg')
)

# Install Data (gnubg/data/...)
install_data(
    'src/gnubgmodule/data/gnubg.weights',
    'src/gnubgmodule/data/gnubg_ts0.bd',
    'src/gnubgmodule/data/gnubg_os0.bd',
    'src/gnubgmodule/data/gnubg_os.db',
    install_dir: join_paths(pkgdir, 'gnubg', 'data')
)

test_env = environment()
# PYTHONPATH points to the build root so 'import gnubg' finds the package
test_env.set('PYTHONPATH', meson.project_build_root())

test('python_tests',
    python3,
    args: ['-m', 'pytest', join_paths(meson.project_source_root(), 'tests')],
    env: test_env,
    workdir: meson.project_source_root()
)