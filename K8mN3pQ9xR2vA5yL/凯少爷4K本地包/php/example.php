<?php
// 示例PHP爬虫脚本
header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? 'home';

switch ($action) {
    case 'home':
        echo json_encode([
            'class' => [
                ['type_id' => '1', 'type_name' => '电影'],
                ['type_id' => '2', 'type_name' => '电视剧']
            ]
        ]);
        break;
    
    case 'category':
        echo json_encode([
            'list' => [
                ['vod_id' => '1', 'vod_name' => '测试视频', 'vod_pic' => '']
            ]
        ]);
        break;
    
    default:
        echo json_encode(['error' => 'Unknown action']);
}
?>