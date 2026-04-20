{
        inputs = {
            nixpkgs.url = "nixpkgs/22.11";
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
                        name = "run_command";
                        hardeningDisable = [ "all" ];
                        buildInputs = with pkgs; [ bashInteractive gitFull openssh curl gzip which gnused gnutar perl findutils coreutils bashInteractive ];
                        shellHook = ''
                            set -eo pipefail
                            cd /home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/opp_workspace/omnetpp-6.3.0 && find . \( -path ./.opp_env -o -path ./ide \) -prune -o -type f -print0 | xargs -0 shasum > /home/samirhff1/Documents/uni/m1/sem1/sistemi/progetto/opp_workspace/omnetpp-6.3.0/.opp_env/postdownload.sha
                        '';
                    };
                };
            });
        }