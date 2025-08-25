<?php
header('Content-Type: application/json');

$pasta = __DIR__;
$ignorar = $_GET['ignorar'] ?? '';

if (!is_dir($pasta)) {
    http_response_code(404);
    echo json_encode([
        'erro' => 'Pasta não encontrada',
        'pasta' => $pasta
    ]);
    exit;
}

try {
    $arquivos = [];

    function listarArquivos($diretorio, &$arquivos, $ignorar, $base) {
        $somente = false;
        if ($ignorar && $ignorar[0] === '!') {
            $somente = substr($ignorar, 1);
        }

        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($diretorio, RecursiveDirectoryIterator::SKIP_DOTS),
            RecursiveIteratorIterator::LEAVES_ONLY
        );

        foreach ($iterator as $item) {
            $ext = strtolower($item->getExtension());
            if (in_array($ext, ['php', 'txt'])) continue; // Ignora .php e .txt

            $full = str_replace('\\', '/', $item->getRealPath());

            if ($somente) {
                if (strpos($full, '/' . $somente . '/') === false) continue;
            } else {
                if ($ignorar && strpos($full, '/' . $ignorar . '/') !== false) continue;
            }

            $rel = ltrim(str_replace(str_replace('\\', '/', $base), '', $full), '/');
            $arquivos[] = [
                'nome' => $rel,
                'hash' => hash_file('sha256', $item->getPathname())
            ];
        }
    }

    $base = rtrim(str_replace('\\', '/', realpath($pasta)), '/') . '/';
    listarArquivos($pasta, $arquivos, $ignorar, $base);

    usort($arquivos, function ($a, $b) {
        return strcasecmp($a['nome'], $b['nome']);
    });

    echo json_encode($arquivos, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'erro' => 'Erro ao ler a pasta',
        'mensagem' => $e->getMessage()
    ]);
}
?>
