# Generate og-image.jpg (1200x630) — Sangkan Clean share / SERP thumbnail
Add-Type -AssemblyName System.Drawing

$root = "C:\Users\User\Projects\sangkan-clean\sangkan-clean-repo"

$W = 1200
$H = 630
$outPath = Join-Path $root "og-image.jpg"
$logoPath = Join-Path $root "logo.png"
$heroPath = Join-Path $root "images\hero-cleaning.jpg"

# Site palette (style.css)
$primary = [System.Drawing.Color]::FromArgb(255, 15, 118, 110)
$primaryDark = [System.Drawing.Color]::FromArgb(255, 17, 94, 89)
$secondary = [System.Drawing.Color]::FromArgb(255, 2, 132, 199)
$dark = [System.Drawing.Color]::FromArgb(255, 15, 23, 42)
$dark2 = [System.Drawing.Color]::FromArgb(255, 30, 41, 59)
$light = [System.Drawing.Color]::FromArgb(255, 248, 250, 252)
$white = [System.Drawing.Color]::White
$muted = [System.Drawing.Color]::FromArgb(255, 100, 116, 139)
$accent = [System.Drawing.Color]::FromArgb(255, 217, 119, 6)

function New-Font($family, $size, [System.Drawing.FontStyle]$style = [System.Drawing.FontStyle]::Regular) {
    return New-Object System.Drawing.Font -ArgumentList @($family, [single]$size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function Draw-GradientBackground($g, $rect) {
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        $rect,
        $light,
        [System.Drawing.Color]::FromArgb(255, 236, 253, 245),
        35.0,
        $true
    )
    $g.FillRectangle($brush, $rect)
    $brush.Dispose()

    # Soft glow blobs (hero-style)
    $path1 = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path1.AddEllipse(820, -80, 420, 420)
    $pb1 = New-Object System.Drawing.Drawing2D.PathGradientBrush $path1
    $pb1.CenterColor = [System.Drawing.Color]::FromArgb(48, 15, 118, 110)
    $pb1.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 15, 118, 110))
    $g.FillPath($pb1, $path1)
    $pb1.Dispose(); $path1.Dispose()

    $path2 = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path2.AddEllipse(900, 280, 360, 360)
    $pb2 = New-Object System.Drawing.Drawing2D.PathGradientBrush $path2
    $pb2.CenterColor = [System.Drawing.Color]::FromArgb(36, 2, 132, 199)
    $pb2.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 2, 132, 199))
    $g.FillPath($pb2, $path2)
    $pb2.Dispose(); $path2.Dispose()
}

function Draw-HeroPanel($g) {
    if (-not (Test-Path $heroPath)) { return }
    $hero = [System.Drawing.Image]::FromFile($heroPath)
    $dest = New-Object System.Drawing.Rectangle 520, 0, 680, $H
    $g.SetClip($dest)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $scale = [Math]::Max($dest.Width / $hero.Width, $dest.Height / $hero.Height)
    $sw = [int]($hero.Width * $scale)
    $sh = [int]($hero.Height * $scale)
    $sx = $dest.X + [int](($dest.Width - $sw) / 2) + 40
    $sy = $dest.Y + [int](($dest.Height - $sh) / 2)
    $g.DrawImage($hero, $sx, $sy, $sw, $sh)
    $g.ResetClip()

    # Left fade + bottom vignette
    $fade = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Rectangle 480, 0, 280, $H),
        [System.Drawing.Color]::FromArgb(240, 248, 250, 252),
        [System.Drawing.Color]::FromArgb(0, 248, 250, 252),
        0.0
    )
    $g.FillRectangle($fade, 480, 0, 280, $H)
    $fade.Dispose()

    $bottom = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Rectangle 520, 380, 680, 250),
        [System.Drawing.Color]::FromArgb(0, 15, 23, 42),
        [System.Drawing.Color]::FromArgb(180, 15, 23, 42),
        90.0
    )
    $g.FillRectangle($bottom, 520, 380, 680, 250)
    $bottom.Dispose()

    $hero.Dispose()
}

function Draw-RoundedRect($g, $x, $y, $w, $h, $radius, $fill, $border, $borderW = 0) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $radius * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    $g.FillPath((New-Object System.Drawing.SolidBrush $fill), $path)
    if ($borderW -gt 0) {
        $g.DrawPath((New-Object System.Drawing.Pen $border, $borderW), $path)
    }
    $path.Dispose()
}

function Draw-FeatureIcon($g, $cx, $cy, $r, $kind) {
    Draw-RoundedRect $g ($cx - $r) ($cy - $r) ($r * 2) ($r * 2) $r $primary $primary 0
    $pen = New-Object System.Drawing.Pen $white, 2.5
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    switch ($kind) {
        "sparkle" {
            $g.DrawLine($pen, $cx, $cy - 8, $cx, $cy + 8)
            $g.DrawLine($pen, $cx - 8, $cy, $cx + 8, $cy)
            $g.DrawLine($pen, $cx - 5, $cy - 5, $cx + 5, $cy + 5)
            $g.DrawLine($pen, $cx + 5, $cy - 5, $cx - 5, $cy + 5)
        }
        "shield" {
            $pts = @(
                [System.Drawing.Point]::new($cx, $cy - 9),
                [System.Drawing.Point]::new($cx + 8, $cy - 4),
                [System.Drawing.Point]::new($cx + 6, $cy + 8),
                [System.Drawing.Point]::new($cx, $cy + 11),
                [System.Drawing.Point]::new($cx - 6, $cy + 8),
                [System.Drawing.Point]::new($cx - 8, $cy - 4)
            )
            $g.DrawPolygon($pen, $pts)
            $g.DrawLine($pen, $cx - 4, $cy + 1, $cx - 1, $cy + 5)
            $g.DrawLine($pen, $cx - 1, $cy + 5, $cx + 5, $cy - 2)
        }
        "team" {
            $g.FillEllipse((New-Object System.Drawing.SolidBrush $white), $cx - 4, $cy - 8, 8, 8)
            $g.DrawArc($pen, $cx - 10, $cy + 1, 20, 12, 0, 180)
            $g.FillEllipse((New-Object System.Drawing.SolidBrush $white), $cx - 13, $cy - 3, 7, 7)
            $g.FillEllipse((New-Object System.Drawing.SolidBrush $white), $cx + 6, $cy - 3, 7, 7)
        }
        "leaf" {
            $g.DrawBezier($pen,
                [System.Drawing.Point]::new($cx, $cy - 9),
                [System.Drawing.Point]::new($cx + 10, $cy - 2),
                [System.Drawing.Point]::new($cx + 8, $cy + 9),
                [System.Drawing.Point]::new($cx, $cy + 9)
            )
            $g.DrawBezier($pen,
                [System.Drawing.Point]::new($cx, $cy - 9),
                [System.Drawing.Point]::new($cx - 10, $cy - 2),
                [System.Drawing.Point]::new($cx - 8, $cy + 9),
                [System.Drawing.Point]::new($cx, $cy + 9)
            )
            $g.DrawLine($pen, $cx, $cy - 9, $cx, $cy + 9)
        }
    }
    $pen.Dispose()
}

$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

Draw-GradientBackground $g (New-Object System.Drawing.Rectangle 0, 0, $W, $H)
Draw-HeroPanel $g

# Content card
Draw-RoundedRect $g 48 48 620 534 28 $white ([System.Drawing.Color]::FromArgb(255, 226, 232, 240)) 1

# Logo + wordmark row
$logo = [System.Drawing.Image]::FromFile($logoPath)
$logoH = 72
$logoW = [int]($logo.Width * ($logoH / [double]$logo.Height))
$g.DrawImage($logo, 78, 78, $logoW, $logoH)

$fontEnBold = New-Font "Segoe UI" 34 ([System.Drawing.FontStyle]::Bold)
$fontEn = New-Font "Segoe UI" 16 ([System.Drawing.FontStyle]::Regular)
$fontThBold = New-Font "Leelawadee UI" 42 ([System.Drawing.FontStyle]::Bold)
$fontTh = New-Font "Leelawadee UI" 28 ([System.Drawing.FontStyle]::Bold)
$fontThSm = New-Font "Leelawadee UI" 17 ([System.Drawing.FontStyle]::Regular)
$fontThFeat = New-Font "Leelawadee UI" 15 ([System.Drawing.FontStyle]::Regular)
$fontPhone = New-Font "Segoe UI" 22 ([System.Drawing.FontStyle]::Bold)

$textX = 78 + $logoW + 18
$g.DrawString("Sangkan", $fontEnBold, (New-Object System.Drawing.SolidBrush $dark), $textX, 82)
$g.DrawString("Clean", $fontEnBold, (New-Object System.Drawing.SolidBrush $primary), $textX + 138, 82)
$text = Get-Content (Join-Path $PSScriptRoot "og-image-text.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$g.DrawString($text.tagline, $fontEn, (New-Object System.Drawing.SolidBrush $muted), $textX, 124)
$g.DrawString($text.headline1, $fontThBold, (New-Object System.Drawing.SolidBrush $primary), 78, 168)
$g.DrawString($text.headline2, $fontTh, (New-Object System.Drawing.SolidBrush $dark), 78, 222)

# Accent line
$g.FillRectangle((New-Object System.Drawing.SolidBrush $primary), 78, 278, 72, 4)

# Features (original copy)
$features = @(
    @{ kind = "sparkle"; text = $text.features[0] },
    @{ kind = "shield"; text = $text.features[1] },
    @{ kind = "team"; text = $text.features[2] },
    @{ kind = "leaf"; text = $text.features[3] }
)

$fy = 300
$colW = 280
foreach ($i in 0..3) {
    $col = $i % 2
    $row = [Math]::Floor($i / 2)
    $fx = 78 + ($col * $colW)
    $fyItem = 300 + ($row * 88)
    Draw-FeatureIcon $g ($fx + 18) ($fyItem + 18) 18 $features[$i].kind
    $g.DrawString($features[$i].text, $fontThFeat, (New-Object System.Drawing.SolidBrush $dark2), ($fx + 44), ($fyItem + 6))
}

# Phone pill
Draw-RoundedRect $g 78 500 320 44 22 $primary $primary 0
$g.DrawString("063-686-5134", $fontPhone, (New-Object System.Drawing.SolidBrush $white), 108, 508)
$g.DrawString("Hotline", (New-Font "Segoe UI" 13 ([System.Drawing.FontStyle]::Regular)), (New-Object System.Drawing.SolidBrush $white), 278, 516)

# Site URL watermark on hero side
$urlFont = New-Font "Segoe UI" 14 ([System.Drawing.FontStyle]::Regular)
$g.DrawString("www.sangkanclean.com", $urlFont, (New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(220, 255, 255, 255))), 860, 582)

$logo.Dispose()
$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose(); $bmp.Dispose()

Write-Output "Wrote $outPath ($W x $H)"
