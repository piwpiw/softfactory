<?php
/**
 * Plugin Name: Bohemian Studio Core
 * Plugin URI: https://piwpiwwp.mycafe24.com
 * Description: Editorial utility blocks and shortcodes for Bohemian Studio.
 * Version: 0.1.0
 * Author: SoftFactory
 * Text Domain: bohemian-studio-core
 */

if (!defined('ABSPATH')) {
    exit;
}

function bohemian_studio_core_style(): void
{
    wp_register_style(
        'bohemian-studio-core',
        plugins_url('core.css', __FILE__),
        [],
        '0.1.0'
    );
    wp_enqueue_style('bohemian-studio-core');
}
add_action('wp_enqueue_scripts', 'bohemian_studio_core_style');

function bohemian_studio_render_ad_slot($atts = []): string
{
    $atts = shortcode_atts([
        'label' => 'Related tools',
        'position' => 'mid'
    ], $atts, 'bohemian_ad_slot');

    return sprintf(
        '<aside class="bs-core-card bs-ad-slot" data-position="%s"><p class="bs-core-kicker">Sponsored</p><strong>%s</strong><p>광고 또는 제휴 슬롯이 이 위치에 렌더링됩니다.</p></aside>',
        esc_attr($atts['position']),
        esc_html($atts['label'])
    );
}
add_shortcode('bohemian_ad_slot', 'bohemian_studio_render_ad_slot');

function bohemian_studio_render_sources($atts, $content = ''): string
{
    return '<section class="bs-core-card bs-sources"><p class="bs-core-kicker">Sources</p>' . do_shortcode(wpautop($content)) . '</section>';
}
add_shortcode('bohemian_sources', 'bohemian_studio_render_sources');

function bohemian_studio_render_update_log($atts, $content = ''): string
{
    return '<section class="bs-core-card bs-update-log"><p class="bs-core-kicker">Update log</p>' . do_shortcode(wpautop($content)) . '</section>';
}
add_shortcode('bohemian_update_log', 'bohemian_studio_render_update_log');

function bohemian_studio_render_disclosure($atts, $content = ''): string
{
    $body = $content ?: '이 글에는 광고 또는 제휴 링크가 포함될 수 있습니다. 판단 기준은 편집팀이 독립적으로 유지합니다.';
    return '<section class="bs-core-card bs-disclosure"><p class="bs-core-kicker">Disclosure</p>' . wpautop(esc_html($body)) . '</section>';
}
add_shortcode('bohemian_disclosure', 'bohemian_studio_render_disclosure');
