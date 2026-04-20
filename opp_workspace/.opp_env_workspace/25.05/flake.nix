{
        inputs = {
            nixpkgs.url = "nixpkgs/25.05";
            flake-utils.url = "github:numtide/flake-utils";
        };
        outputs = { self, nixpkgs, flake-utils }:
        flake-utils.lib.eachDefaultSystem(system:
        let
            overlay = final: prev: {
                # allow python2 to be installed despite being EOL and having known vulnerabilities
                python2 = prev.python2.overrideAttrs (oldAttrs: {
                    meta = oldAttrs.meta // { knownVulnerabilities = []; };
                });
            };
            pkgs = import nixpkgs { inherit system; overlays = [ overlay ]; };
            in rec {
                devShells = rec {
                    default = pkgs.llvmPackages.stdenv.mkDerivation {
                        name = "omnetpp-6.3.0";
                        hardeningDisable = [ "all" ];
                        buildInputs = with pkgs; [ graphviz doxygen gtk3 glib glib-networking libsecret cairo freetype fontconfig xorg.libXtst xorg.libX11 xorg.libXrender adw-gtk3 gsettings-desktop-schemas zlib webkitgtk_4_1 stdenv.cc stdenv.cc.cc.lib qt6.qtbase qt6.qtsvg qt6.qtwayland qt6ct adwaita-qt6 kdePackages.breeze llvmPackages.bintools bison flex perl libxml2 expat which xdg-utils pkg-config ccache gnumake42 vim libdwarf elfutils python3 lldb python3Packages.numpy python3Packages.scipy python3Packages.pandas python3Packages.matplotlib python3Packages.posix_ipc python3Packages.pyqt6 python3Packages.packaging python3Packages.ipython bashInteractive gitFull openssh curl gzip gnused gnutar findutils coreutils bashInteractive ];
                        shellHook = ''
                            set -eo pipefail
                            function error() { echo "$*" 1>&2; return 1; }; export -f error
function ll() { ls -l $*; }; export -f ll
export BUILD_MODES="release debug"
export OPP_ENV_DIR="/home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/.venv/lib/python3.12/site-packages/opp_env"
export OPP_ENV_VERSION="0.35.0.251114"
export OPP_ENV_PROJECTS="omnetpp-6.3.0"
export OPP_ENV_PROJECT_DEPS="omnetpp-6.3.0: "
export OMNETPP_ROOT=/home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/opp_workspace/omnetpp-6.3.0
export OMNETPP_VERSION="6.3.0"
export QT_PLUGIN_PATH=${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}:${pkgs.qt6.qtsvg}/${pkgs.qt6.qtbase.qtPluginPrefix}
export QT_PLUGIN_PATH=$QT_PLUGIN_PATH:${pkgs.qt6.qtwayland}/${pkgs.qt6.qtbase.qtPluginPrefix}
export QT_PLUGIN_PATH=$QT_PLUGIN_PATH:${pkgs.kdePackages.breeze}/lib/qt-6/plugins
export QT_PLUGIN_PATH=$QT_PLUGIN_PATH:${pkgs.adwaita-qt6}/lib/qt-6/plugins
export QT_QPA_PLATFORMTHEME=qt6ct
export GTK_THEME=Adwaita
export QT_XCB_GL_INTEGRATION=''${QT_XCB_GL_INTEGRATION:-none}  # disable GL support as NIX does not play nicely with OpenGL (except on nixOS)
export NIX_CFLAGS_COMPILE="$NIX_CFLAGS_COMPILE -isystem ${pkgs.libxml2.dev}/include/libxml2"
export XDG_DATA_DIRS=$XDG_DATA_DIRS:$GSETTINGS_SCHEMAS_PATH
export GIO_EXTRA_MODULES=${pkgs.glib-networking}/lib/gio/modules
pushd . > /dev/null
cd '/home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/opp_workspace/omnetpp-6.3.0'
source setenv
export OPP_RUN_DBG_BIN=$OMNETPP_ROOT/bin/opp_run_dbg; export OPP_RUN_RELEASE_BIN=$OMNETPP_ROOT/bin/opp_run_release
popd > /dev/null

                function build_omnetpp ()
                {
                    modes="$*"
                    modes=''${modes:-$BUILD_MODES}
                    modes=''${modes:-release debug}

                    (
                        for mode in $modes; do
                            echo -e "\033[0;32mInvoking build_omnetpp $mode:\033[0;0m"
                            cd $OMNETPP_ROOT
                            BUILD_MODE=$mode
                            true ============== Project-specific commands: ==============
                            { [ config.status -nt configure.user ] || ./configure && make -j$NIX_BUILD_CORES MODE=$BUILD_MODE; } || exit $?
                            true ========================================================
                        done
                    )

                    if [ "$?" == "0" ]; then
                        echo -e "\033[0;32mDone build_omnetpp $mode\033[0;0m"
                    else
                        echo -e "\033[1;31mERROR in build_omnetpp $mode\033[0;0m";
                        return 1
                    fi
                }
                export -f build_omnetpp
            

                function clean_omnetpp ()
                {
                    modes="$*"
                    modes=''${modes:-$BUILD_MODES}
                    modes=''${modes:-release debug}

                    (
                        for mode in $modes; do
                            echo -e "\033[0;32mInvoking clean_omnetpp $mode:\033[0;0m"
                            cd $OMNETPP_ROOT
                            BUILD_MODE=$mode
                            true ============== Project-specific commands: ==============
                            { make clean MODE=$BUILD_MODE; } || exit $?
                            true ========================================================
                        done
                    )

                    if [ "$?" == "0" ]; then
                        echo -e "\033[0;32mDone clean_omnetpp $mode\033[0;0m"
                    else
                        echo -e "\033[1;31mERROR in clean_omnetpp $mode\033[0;0m";
                        return 1
                    fi
                }
                export -f clean_omnetpp
            

                function smoke_test_omnetpp ()
                {
                    modes="$*"
                    modes=''${modes:-$BUILD_MODES}
                    modes=''${modes:-release debug}

                    (
                        for mode in $modes; do
                            echo -e "\033[0;32mInvoking smoke_test_omnetpp $mode:\033[0;0m"
                            cd $OMNETPP_ROOT
                            BUILD_MODE=$mode
                            true ============== Project-specific commands: ==============
                            { if [ "$BUILD_MODE" = "debug" ]; then DEBUG_SUFFIX="_dbg"; fi ; } || exit $?
{ cd samples/dyna; ./dyna$DEBUG_SUFFIX -u Cmdenv; } || exit $?
                            true ========================================================
                        done
                    )

                    if [ "$?" == "0" ]; then
                        echo -e "\033[0;32mDone smoke_test_omnetpp $mode\033[0;0m"
                    else
                        echo -e "\033[1;31mERROR in smoke_test_omnetpp $mode\033[0;0m";
                        return 1
                    fi
                }
                export -f smoke_test_omnetpp
            

                function test_omnetpp ()
                {
                    modes="$*"
                    modes=''${modes:-$BUILD_MODES}
                    modes=''${modes:-release debug}

                    (
                        for mode in $modes; do
                            echo -e "\033[0;32mInvoking test_omnetpp $mode:\033[0;0m"
                            cd $OMNETPP_ROOT
                            BUILD_MODE=$mode
                            true ============== Project-specific commands: ==============
                            { cd test/core; MODE=$BUILD_MODE ./runtest; } || exit $?
                            true ========================================================
                        done
                    )

                    if [ "$?" == "0" ]; then
                        echo -e "\033[0;32mDone test_omnetpp $mode\033[0;0m"
                    else
                        echo -e "\033[1;31mERROR in test_omnetpp $mode\033[0;0m";
                        return 1
                    fi
                }
                export -f test_omnetpp
            

                function check_omnetpp ()
                {
                    (
                    echo -e "\033[0;32mInvoking check_omnetpp:\033[0;0m"
                    echo 'Checking whether files have changed since download...'
                    cd $OMNETPP_ROOT
                    tmp=.opp_env/postdownload_changes.txt
                    if shasum --check --quiet .opp_env/postdownload.sha > $tmp 2>/dev/null; then
                        echo OK
                    else
                        cat $tmp | sed 's/FAILED open or read/MISSING/; s/FAILED$/MODIFIED/'
                        echo -e "\033[1;33mWARNING:\033[0;0m omnetpp-6.3.0: $(cat $tmp | wc -l) file(s) changed since download"
                    fi
                    rm $tmp
                    )
                }
                export -f check_omnetpp
            
function build_all() {
                { build_omnetpp "$@" || return 1; } || exit $?
            }
            export -f build_all
function clean_all() {
                { clean_omnetpp "$@" || return 1; } || exit $?
            }
            export -f clean_all
function smoke_test_all() {
                { smoke_test_omnetpp "$@"; } || exit $?
            }
            export -f smoke_test_all
function test_all() {
                { test_omnetpp "$@"; } || exit $?
            }
            export -f test_all
function check_all() {
                { check_omnetpp "$@"; } || exit $?
            }
            export -f check_all
function opp_env() {
                { printf 'error: Cannot run opp_env commands in an opp_env shell -- exit the shell to run it.
' && return 1; } || exit $?
            }
            export -f opp_env

  cd omnetpp-6.3.0 &&
  source setenv &&
  omnetpp

                        '';
                    };
                };
            });
        }