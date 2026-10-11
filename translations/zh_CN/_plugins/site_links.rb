# frozen_string_literal: true

require "addressable/uri"
require "date"
require "nokogiri"
require "yaml"

module Gem5Chinese
  # Resolve only known pages. A typo must remain a build-check failure rather
  # than being turned into an equally broken URL on the English website.
  class SiteLinks
    attr_reader :fallbacks

    def initialize(site)
      @site = site
      @baseurl = site.baseurl.to_s.sub(%r{/$}, "")
      @origin = site.config.fetch("url").sub(%r{/$}, "")
      @english = site.config.fetch("english_url").sub(%r{/$}, "")
      @host = Addressable::URI.parse(@origin).host
      @local = {}
      (site.pages + site.documents).each do |page|
        @local[key(page.url)] = page.url if page.respond_to?(:output_ext) && page.output_ext == ".html"
      end
      static_files = site.static_files + site.collections.values.flat_map(&:files)
      @static = static_files.to_h { |file| [file.url, true] }
      @upstream = {}
      @fallbacks = Hash.new(0)
      upstream = File.expand_path("../..", site.source)
      Dir.glob(File.join(upstream, "_pages", "**", "*.{md,html}")).sort.each do |file|
        data = front_matter(file)
        next unless data["permalink"]

        url = "/" + data["permalink"].sub(%r{^/+}, "")
        @upstream[key(url)] = url
      end
    end

    def rewrite(page)
      html = Nokogiri::HTML5.parse(page.output)
      changed = false
      html.css("[href], [src], [action], [poster]").each do |node|
        %w[href src action poster].each do |attribute|
          next unless node[attribute]

          target, fallback = resolve(node[attribute], page.url)
          next unless target

          changed ||= target != node[attribute]
          node[attribute] = target
          next unless fallback

          @fallbacks[target] += 1
          node["data-english-fallback"] = "true"
          if node.name == "a"
            node["hreflang"] = "en"
            node["title"] = [node["title"], "尚无中文译文，查看官方英文文档"].compact.join("；")
            node.add_child('<span class="english-link-label">（英文）</span>')
          end
          changed = true
        end
      end
      page.output = html.to_html if changed
    end

    def resolve(href, page_url)
      return if href.empty? || href.start_with?("#")

      uri = Addressable::URI.join(@origin + @baseurl + page_url, href)
      return unless %w[http https].include?(uri.scheme) && uri.host == @host

      path = Addressable::URI.unencode(uri.path)
      path = path.delete_prefix(@baseurl) if path == @baseurl || path.start_with?(@baseurl + "/")
      suffix = (uri.query ? "?#{uri.query}" : "") + (uri.fragment ? "##{uri.fragment}" : "")
      if (local = @local[key(path)])
        [@baseurl + local + suffix, false]
      elsif @static[path]
        [@baseurl + Addressable::URI.normalize_component(path, Addressable::URI::CharacterClasses::PATH) + suffix, false]
      elsif (english = @upstream[key(path)])
        [@english + english + suffix, true]
      end
    rescue Addressable::URI::InvalidURIError
      # The independent output checker reports malformed/unresolved local URLs.
      nil
    end

    private

    def key(path)
      path.sub(%r{/index\.html$}, "/").sub(%r{/$}, "")
    end

    def front_matter(file)
      header = +""
      File.open(file, "r:utf-8") do |input|
        return {} unless input.gets&.strip == "---"

        input.each_line do |line|
          break if ["---", "..."].include?(line.strip)

          header << line
        end
      end
      YAML.safe_load(header, permitted_classes: [Date, Time], aliases: true) || {}
    end
  end
end

Jekyll::Hooks.register :site, :pre_render do |site|
  site.config["zh_site_links"] = Gem5Chinese::SiteLinks.new(site)
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |page|
  page.site.config.fetch("zh_site_links").rewrite(page) if page.output_ext == ".html"
end

Jekyll::Hooks.register :site, :post_write do |site|
  fallbacks = site.config.fetch("zh_site_links").fallbacks
  Jekyll.logger.info "Chinese links:", "#{fallbacks.values.sum} references use #{fallbacks.size} English pages"
end
