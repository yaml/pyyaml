# TODO: run in PR/test mode (larger matrix) vs "all-in-one" artifact/packaging mode
# TODO: use dynamic matrix so PRs are multi-job and tag builds are one (consolidate artifacts)
# TODO: consider secure credential storage for inline upload on tags? Or keep that all manual/OOB for security...
# TODO: refactor libyaml/pyyaml tests to enable first-class output for AppVeyor
# TODO: get version number from setup.py and/or lib(3)/__version__
# Update-AppveyorBuild -Version $dynamic_version

Function Invoke-Exe([scriptblock]$sb) {
    & $sb
    $exitcode = $LASTEXITCODE
    If($exitcode -ne 0) {
       throw "exe failed with nonzero exit code $exitcode"
    }
}

Function Bootstrap() {
<#
    # ensure python 3.9 prerelease is present (current Appveyor VS2015 image doesn't include it)
    If(-not $(Test-Path C:\Python39)) {
        Invoke-Exe { choco.exe install python3 --version=3.9.0-a1 --forcex86 --force --params="/InstallDir:C:\Python39" --no-progress }
    }

    If(-not $(Test-Path C:\Python39-x64)) {
        Invoke-Exe { choco.exe install python3 --version=3.9.0-a1 --force --params="/InstallDir:C:\Python39-x64" --no-progress }
    }
#>
    Write-Output "patching Windows SDK bits for distutils"

    # patch 7.0/7.1 vcvars SDK bits up to work with distutils query
    Set-Content -Path 'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\amd64\vcvarsamd64.bat' '@CALL "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\vcvars64.bat"'
    Set-Content -Path 'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\bin\amd64\vcvars64.bat' '@CALL "C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\SetEnv.cmd" /Release /x64'

    # patch VS9 x64 CMake config for VS Express, hide `reg.exe` stderr noise
    Invoke-Exe { $noise = reg.exe import packaging\build\FixVS9CMake.reg 2>&1 }

    Copy-Item -Path "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcpackages\AMD64.VCPlatform.config" -Destination "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcpackages\AMD64.VCPlatform.Express.config" -Force
    Copy-Item -Path "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcpackages\Itanium.VCPlatform.config" -Destination "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcpackages\Itanium.VCPlatform.Express.config" -Force

    # git spews all over stderr unless we tell it not to
    $env:GIT_REDIRECT_STDERR="2>&1"; 

    $libyaml_repo_url = If($env:libyaml_repo_url) { $env:libyaml_repo_url } Else { "https://github.com/yaml/libyaml.git" }
    $libyaml_refspec = If($env:libyaml_refspec) { $env:libyaml_refspec } Else { "master" }
    
    Write-Output "cloning libyaml from $libyaml_repo_url / $libyaml_refspec"

    If(-not $(Test-Path .\libyaml)) {
        Invoke-Exe { git clone -b $libyaml_refspec $libyaml_repo_url 2>&1 }
    }
}

Function Build-Wheel($python_path) {

    #$python_path = Join-Path C:\ $env:PYTHON_VER
    $python = Join-Path $python_path python.exe

    Write-Output "building pyyaml wheel for $python_path"

    # query distutils for the VC version used to build this Python; translate to a VS version to choose the right generator
    $python_vs_buildver = Invoke-Exe { & $python -c "from distutils.version import LooseVersion; from distutils.msvc9compiler import get_build_version; print(LooseVersion(str(get_build_version())).version[0])" }

    $python_cmake_generator = switch($python_vs_buildver) {
        "9" { "Visual Studio 9 2008" }
        "10" { "Visual Studio 10 2010" }
        "14" { "Visual Studio 14 2015" }
        default { throw "Python was built with unknown VS build version: $python_vs_buildver" }
    }

    # query arch this python was built for
    $python_arch = Invoke-Exe { & $python -c "from distutils.util import get_platform; print(str(get_platform()))" }

    if($python_arch -eq 'win-amd64') {
        $python_cmake_generator += " Win64"
        $vcvars_arch = "x64"
    }

    # snarf VS vars (paths, etc) for the matching VS version and arch that built this Python
    $raw_vars_out = Invoke-Exe { cmd.exe /c "`"C:\Program Files (x86)\Microsoft Visual Studio $($python_vs_buildver).0\VC\vcvarsall.bat`" $vcvars_arch & set" }
    foreach($kv in $raw_vars_out) {
        If($kv -match "=") {
            $kv = $kv.Split("=", 2)
            Set-Item -Force "env:$kv[0]" $kv[1]
        }
        Else {
            Write-Output $kv
        }
    }

    # ensure pip is current (some appveyor pips are not)
    Invoke-Exe { & $python -W "ignore:DEPRECATION" -m pip install --upgrade pip }

    # ensure required-for-build packages are present and up-to-date
    Invoke-Exe { & $python -W "ignore:DEPRECATION" -m pip install --upgrade cython wheel setuptools --no-warn-script-location }

    pushd libyaml
    Invoke-Exe { git clean -fdx }
    popd

    mkdir libyaml\build

    pushd libyaml\build
    Invoke-Exe { cmake.exe -G $python_cmake_generator -DYAML_STATIC_LIB_NAME=yaml .. }
    Invoke-Exe { cmake.exe --build . --config Release }
    popd

    Invoke-Exe { & $python setup.py --with-libyaml build_ext -I libyaml\include -L libyaml\build\Release -D YAML_DECLARE_STATIC build test bdist_wheel }
}

Function Upload-Artifacts() {
    Write-Output "uploading artifacts..."

    foreach($wheel in @(Resolve-Path dist\*.whl)) {
        Push-AppveyorArtifact $wheel
    }
}

Bootstrap

$pythons = @(
"C:\Python27"
"C:\Python27-x64"
"C:\Python35"
"C:\Python35-x64"
"C:\Python36"
"C:\Python36-x64"
"C:\Python37"
"C:\Python37-x64"
"C:\Python38"
"C:\Python38-x64"
)

#$pythons = @("C:\$($env:PYTHON_VER)")

foreach($python in $pythons) {
    Build-Wheel $python
}

Upload-Artifacts
