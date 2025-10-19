# SAFT Doctor - Push to GitHub Script
# Este script facilita o push inicial do projeto para o GitHub

Write-Host "🏥 SAFT Doctor - GitHub Push Helper" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Verificar se estamos no diretório correto
if (-not (Test-Path ".git")) {
    Write-Host "❌ Erro: Este script deve ser executado na raiz do projeto git" -ForegroundColor Red
    exit 1
}

# Verificar se já existe remote
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "⚠️  Remote 'origin' já existe:" -ForegroundColor Yellow
    git remote -v
    Write-Host ""
    $resposta = Read-Host "Deseja remover e reconfigurar? (s/n)"
    if ($resposta -eq "s" -or $resposta -eq "S") {
        git remote remove origin
        Write-Host "✅ Remote removido" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Mantendo configuração atual" -ForegroundColor Blue
        exit 0
    }
}

# Solicitar URL do repositório
Write-Host "`n📝 Por favor, crie um repositório no GitHub:" -ForegroundColor Cyan
Write-Host "   1. Vá para https://github.com/new" -ForegroundColor White
Write-Host "   2. Nome do repositório: saft-doctor" -ForegroundColor White
Write-Host "   3. NÃO inicialize com README, .gitignore ou LICENSE" -ForegroundColor Yellow
Write-Host "   4. Clique em 'Create repository'`n" -ForegroundColor White

$repoUrl = Read-Host "Cole a URL do repositório (ex: https://github.com/usuario/saft-doctor.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "❌ URL não pode estar vazia" -ForegroundColor Red
    exit 1
}

# Adicionar remote
Write-Host "`n🔗 Adicionando remote origin..." -ForegroundColor Cyan
git remote add origin $repoUrl

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Remote adicionado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao adicionar remote" -ForegroundColor Red
    exit 1
}

# Mostrar branches disponíveis
Write-Host "`n📋 Branches disponíveis:" -ForegroundColor Cyan
git branch

# Fazer push da branch main
Write-Host "`n🚀 Fazendo push da branch main..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Branch main enviada com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao fazer push da branch main" -ForegroundColor Red
    exit 1
}

# Fazer push da branch develop
Write-Host "`n🚀 Fazendo push da branch develop..." -ForegroundColor Cyan
git push -u origin develop

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Branch develop enviada com sucesso" -ForegroundColor Green
} else {
    Write-Host "⚠️  Branch develop não foi enviada (pode não existir)" -ForegroundColor Yellow
}

# Instruções finais
Write-Host "`n🎉 Push concluído com sucesso!" -ForegroundColor Green
Write-Host "`n📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Acesse: $repoUrl" -ForegroundColor White
Write-Host "   2. Clique em 'Pull requests' → 'New pull request'" -ForegroundColor White
Write-Host "   3. Base: main ← Compare: develop" -ForegroundColor White
Write-Host "   4. Use o conteúdo de .github/pr-description.md como descrição" -ForegroundColor White
Write-Host "   5. Revise e submeta o PR!" -ForegroundColor White

Write-Host "`n📝 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   Ver PR description: cat .github/pr-description.md" -ForegroundColor White
Write-Host "   Criar PR via CLI: gh pr create --base main --head develop" -ForegroundColor White
Write-Host "   Ver repositório: git remote -v" -ForegroundColor White

Write-Host "`n✨ Happy coding! 🚀" -ForegroundColor Green