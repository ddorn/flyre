{ pkgs? import <nixpkgs> {}, ... }:
with pkgs;

let
  customPython = pkgs.python38.buildEnv.override {
    extraLibs = with pkgs.python38Packages; [
      pygame
    ];
  };
in
  mkShell {
    buildInputs = [
      customPython
    ];
  }
