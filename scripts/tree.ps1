function Show-Tree($path, $prefix = "") {
    $skip = ".venv", "__pycache__", ".git", ".pytest_cache", "structure.txt"
    $items = @(Get-ChildItem -LiteralPath $path -Force |
        Where-Object { $skip -notcontains $_.Name } |
        Sort-Object @{Expression={-not $_.PSIsContainer}}, Name)
    for ($i = 0; $i -lt $items.Count; $i++) {
        $last = ($i -eq $items.Count - 1)
        $branch = if ($last) { "\-- " } else { "+-- " }
        "$prefix$branch$($items[$i].Name)"
        if ($items[$i].PSIsContainer) {
            $ext = if ($last) { "    " } else { "|   " }
            Show-Tree $items[$i].FullName ($prefix + $ext)
        }
    }
}
$out = @((Split-Path -Leaf (Get-Location)))
$out += Show-Tree (Get-Location).Path
$out | Out-File structure.txt -Encoding utf8