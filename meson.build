# meson.build
project(
    'gnubg-nn',                      # Your project name
    ['cpp', 'c'],                 # Languages used
    version: run_command(
        ['src/_build_utils/_version.py'],
        check: true
    ).stdout().strip(),
    meson_version : '>=1.7.0',     # Require a recent Meson
)

python3 = import('python').find_installation('python3', pure: false)
python_dep = python3.dependency()
pkgdir = python3.get_install_dir()
pkg_name = 'gnubg_nn'

# Custom target to generate __version__.py at build time and install it
generate_version = custom_target(
    'generate_version',
    output: '__version__.py',
    command: [
        python3,
        files('src/_build_utils/_version.py'),
        '--write', '@OUTPUT@'
    ],
    build_by_default: true,
    install: true,
    install_dir: join_paths(pkgdir, pkg_name)
)

# Install __init__.py
install_data(
    'src/gnubgmodule/__init__.py',
    install_dir: join_paths(pkgdir, pkg_name)
)
# Install gnubg.pyi
install_data(
    'src/gnubgmodule/bindings.pyi',
    install_dir: join_paths(pkgdir, 'gnubg_nn')
)

install_data(
    'src/gnubgmodule/data/gnubg.weights',
    'src/gnubgmodule/data/gnubg_ts0.bd',
    'src/gnubgmodule/data/gnubg_os0.bd',
    'src/gnubgmodule/data/gnubg_os.db',
    install_dir: join_paths(pkgdir, pkg_name, 'data')
)

conf_data = configuration_data()
conf_data.set('_CRT_SECURE_NO_WARNINGS', 1)  # or 0 to disable
conf_data.set('NOMINMAX', 1)
conf_data.set('LOADED_BO', 1)
conf_data.set('OS_BEAROFF_DB', 1)
conf_data.set('HAVE_CONFIG_H', 1)

config_h = configure_file(
    output: 'config.h',
    configuration: conf_data
)

add_project_arguments(
    '-include', 'config.h',
    language: ['c', 'cpp']
)

# Include directories
gnubg_inc = include_directories(
    'src/gnubg-nn',
    'src/gnubg-nn/gnubg',
    'src/gnubg-nn/gnubg/lib',
    'src/gnubg-nn/analyze',
    'src/gnubg-nn/py',
)

# C sources
c_sources = files(
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

# C++ sources
cpp_sources = files(
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

# Build static library bundling all GNUBG engine code
libgnubg_nn = static_library(
    'gnubg_nn',
    c_sources + cpp_sources,
    include_directories : gnubg_inc,
    cpp_args            : ['-std=c++14', '-Wno-unused-but-set-variable'],
    install             : false,
    dependencies:       [python_dep],  # ✅ use the Python headers!
)

# Force-link every object to avoid missing-symbol errors
gnubg_dep = declare_dependency(
    include_directories : gnubg_inc,
    link_with           : libgnubg_nn,
).as_link_whole()

# Build the Python extension
py_ext = python3.extension_module(
    '_gnubg_nn',              # Name becomes 'nn'
    [],
    dependencies : [gnubg_dep],
    install      : true,
    subdir       : 'gnubg_nn', # Placed inside the 'gnubg' folder
)

test_env = environment()
test_env.set('PYTHONPATH', [meson.project_build_root()])

test('python_tests',
    python3,
    args: ['-m', 'pytest', join_paths(meson.project_source_root(), 'tests')],
    env: test_env,
    workdir: meson.project_source_root()
)