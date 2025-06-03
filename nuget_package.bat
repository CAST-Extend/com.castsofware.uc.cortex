@echo off
set nugetexe=C:\Program Files\Nuget\nuget.exe
set EnableNugetPackageRestore=true
"%nugetexe%" pack plugin.nuspec -ExcludeEmptyDirectories