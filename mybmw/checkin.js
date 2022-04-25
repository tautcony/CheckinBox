import axios from "axios";
import crypto from "crypto";
import url from "url";
import fs from "fs";
import { dirname } from 'path';
import { fileURLToPath } from 'url';
import readline from "readline";

import libsodium from "libsodium-wrappers";
import { Octokit } from "@octokit/rest";


const MYBMW_VERSION = '2.3.0(13603)';
const BMW_SERVER_HOST = 'https://myprofile.bmw.com.cn';

const API_PUBLIC_KEY = '/eadrax-coas/v1/cop/publickey';
const API_LOGIN = '/eadrax-coas/v1/login/pwd';
const API_REFRESH_TOKEN = '/eadrax-coas/v1/oauth/token';
const API_CHECK_IN = '/cis/eadrax-community/private-api/v1/mine/check-in';
const API_ARTICLE_LIST = '/cis/eadrax-ocommunity/public-api/v1/article-list';
const API_SHARE_ARTICLE = '/cis/eadrax-oarticle/open/article/api/v2/share-article';
const API_JOY_INFO = '/cis/eadrax-membership/api/v1/joy-info';
const API_JOY_LIST = '/cis/eadrax-membership/api/v2/joy-list';


const fetch = axios.create({
    timeout: 5000,
    baseURL: BMW_SERVER_HOST,
    headers: {
        'User-Agent': 'Dart/2.10 (dart:io)',
        'x-user-agent': `ios(15.4.1);bmw;${MYBMW_VERSION}`,
        'Accept-Language': 'zh-CN',
        'host': 'myprofile.bmw.com.cn',
        'content-type': 'application/json; charset=utf-8'
    }
});

fetch.interceptors.response.use(function (response) {
    const data = response.data || {};
    if (data.code < 200 || data.code > 299) {
        console.warn(`请求接口 "${response.request.path}" 失败:`, response.data);
    }
    return data;
}, function (error) {
    console.log(`请求接口 "${error.request.path}" 失败: ${error.message}`);
    return {
        data: {
            code: error.response.status,
            error: true,
            message: error.message
        }
    };
});


/**
 * 加密密码
 * @param {string} text 原文
 * @param {string} publicKey 共钥
 * @returns {string} 密文
 */
function rsa_encrypt(text, publicKey) {
    const encryptedData = crypto.publicEncrypt(
        {
            key: publicKey,
            padding: crypto.constants.RSA_PKCS1_PADDING,
        },
        Buffer.from(text)
    );
    return encryptedData.toString('base64');
}

class GithubSecret {
    owner;
    repo;

    constructor() {
        const github_repository =process.env["GITHUB_REPOSITORY"].split("/");
        this.owner = github_repository[0];
        this.repo = github_repository[1];
        
        const github_token = process.env["ACCESS_TOKEN"];
        this.octokit = new Octokit({ auth: github_token });
    }

    /**
     * 获取公钥
     * @returns {Promise<{key_id: string, key: string}>} 公钥
     */
    async get_public_key() {
        return this.octokit.request('GET /repos/{owner}/{repo}/actions/secrets/public-key', {
            owner: this.owner,
            repo: this.repo
        });
    }

    /**
     * 加密 github secret
     * @param {string} value 原文
     * @param {string} key 公钥
     * @returns {Promise<string>} 密文
     */
    async secret_encrypt(value, key) {
        console.log(typeof value, typeof key);

        const keyBytes = Buffer.from(key, 'base64');
        const messageBytes = Buffer.from(value);
    
        await libsodium.ready;
        const encryptedBytes = libsodium.crypto_box_seal(messageBytes, keyBytes);
        const encrypted = Buffer.from(encryptedBytes).toString('base64');
    
        return encrypted;
    }

    /**
     * 更新 github secret
     * @param {string} secret_name secret名称
     * @param {string} value 密文
     * @param {string} key_id 公钥id
     * @returns 
     */
    async write_secret(secret_name, value, key_id) {
        return this.octokit.request('PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}', {
            owner: this.owner,
            repo: this.repo,
            secret_name,
            encrypted_value: value,
            key_id
        });
    }
}


/**
 * 获取用户名与密码
 * @returns {Promise<{username: string, password: string}>}
 */
async function fetch_userinfo() {
    const cio = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    // eslint-disable-next-line no-unused-vars
    return new Promise((resolve, reject) => {
        cio.question('username: ', username => {
            // eslint-disable-next-line no-unused-vars
            cio.input.on("keypress", function (c, k) {
                const len = cio.line.length;
                readline.moveCursor(cio.output, -len, 0);
                readline.clearLine(cio.output, 1);
                for (let i = 0; i < len; i++) {
                  cio.output.write("*");
                }
            });
            cio.question('password: ', password => {
                cio.close();
                resolve({
                    username,
                    password
                });
            });
        });
    });
}

class myBMWClient {
    access_token;
    refresh_token;
    token_type;

    constructor() {
        this.access_token = undefined;
        this.refresh_token = undefined;
        this.token_type = undefined;
    }

    /**
     * 从服务器获取公钥
     * @returns {Promise<{data: {value: string, expires: number }, code: number, error: boolean}>}
     */
    async get_public_key() {
        return fetch.get(`${BMW_SERVER_HOST}${API_PUBLIC_KEY}`);
    }
    
    /**
     * 从服务器获取token
     * @param {string} mobile 用户名
     * @param {string} password 密码
     * @returns {Promise<{data: {access_token: string, refresh_token: string, token_type: string}, code: number, error: boolean}>}
     */
    async get_token(mobile, password) {
        if (!mobile || !password) {
            throw new Error('mobile or password is empty');
        }
        const rsa_resp = await this.get_public_key();
        const public_key = rsa_resp.data.value;
        const encrypt_password = rsa_encrypt(password, public_key);
        const payload = {
            'mobile': mobile,
            'password': encrypt_password,
        }
        const resp = await fetch.post(`${BMW_SERVER_HOST}${API_LOGIN}`, payload);
        this.access_token = resp.data.access_token;
        this.refresh_token = resp.data.refresh_token;
        this.token_type = resp.data.token_type;

        return resp;
    }

    /**
     * 校验token是否有效
     * @param {string} token Token
     * @returns {boolean} 是否有效
     */
    is_token_expired(token) {
        if (!token) {
            return true;
        }
        const payload = Buffer.from(token.split('.')[1], 'base64').toString('utf8');
        const expiry = JSON.parse(payload).exp;
        return (Math.floor((new Date).getTime() / 1000)) >= expiry;
    }

    /**
     * 使用refresh_token刷新token
     * @returns {Promise<{data: {access_token: string, refresh_token: string, token_type: string}, code: number, error: boolean}>}
     */
    async refresh_access_token() {
        const payload = {
            'grant_type': 'refresh_token',
            'refresh_token': this.refresh_token
        }
        const resp = await fetch.post(`${BMW_SERVER_HOST}${API_REFRESH_TOKEN}`, new url.URLSearchParams(payload).toString());
        this.access_token = resp.data.access_token;
        this.refresh_token = resp.data.refresh_token;
        this.token_type = resp.data.token_type;
        return resp;
    }

    /**
     * 从外部加载token等信息
     * @param {boolean} is_github_action 是否是github action中
     */
    async load_token(is_github_action) {
        if (is_github_action) {
            this.access_token = process.env['BMW_ACCESS_TOKEN'];
            this.refresh_token = process.env['BMW_REFRESH_TOKEN'];
            if (!this.access_token || !this.refresh_token) {
                console.log("BMW_ACCESS_TOKEN or BMW_REFRESH_TOKEN is empty, please check your environment variables");
                throw new Error('github action require access_token to work');
            }
            if (await this.init_token(undefined, undefined)) {
                const github = new GithubSecret();
                const key_info = await github.get_public_key();
                const access_token_encrypted = await github.secret_encrypt(this.access_token, key_info.data.key);
                const refresh_token_encrypted = await github.secret_encrypt(this.refresh_token, key_info.data.key);
                await github.write_secret('BMW_ACCESS_TOKEN', access_token_encrypted, key_info.data.key_id);
                await github.write_secret('BMW_REFRESH_TOKEN', refresh_token_encrypted, key_info.data.key_id);
            }
        } else {
            const __dirname = dirname(fileURLToPath(import.meta.url));
            let username = undefined;
            let password = undefined;
            if (!fs.existsSync(__dirname + '/token.json')) {
                const ret = await fetch_userinfo();
                username = ret.username;
                password = ret.password;
            } else {
                const storage = JSON.parse(fs.readFileSync(__dirname + '/token.json'));
                this.access_token = storage['BMW_ACCESS_TOKEN'];
                this.refresh_token = storage['BMW_REFRESH_TOKEN'];
            }
            if (await this.init_token(username, password)) {
                fs.writeFileSync(__dirname + '/token.json', JSON.stringify({
                    'BMW_ACCESS_TOKEN': this.access_token,
                    'BMW_REFRESH_TOKEN': this.refresh_token
                }, undefined, 4));
            }
        }
        if (!this.access_token) {
            throw new Error('access_token is empty');
        }
    }

    /**
     * 初始化token
     * @param {string} username 用户名
     * @param {string} password 密码
     * @returns {Promise<boolean>} 是否初始化成功
     */
    async init_token(username, password) {
        if (!this.is_token_expired(this.access_token)) {
            console.log("accsess token is fine");
        } else if (!this.is_token_expired(this.refresh_token)) {
            this.access_token = undefined;
            console.log("access token expired, refresh token...");
            await this.refresh_access_token();
        } else {
            this.access_token = undefined;
            this.refresh_token = undefined;
            console.log("all token expired, fetch new token...");
            await this.get_token(username, password);
        }

        if (this.access_token) {
            console.log("init token success");
            fetch.defaults.headers.common['Authorization'] = `Bearer ${this.access_token}`;
            return true;
        }
        console.log("init token failed");
        return false;
    }

    /**
     * 执行签到操作
     * @returns 
     */
    async check_in() {
        const payload = {"signDate":null};
        const resp = await fetch.post(`${BMW_SERVER_HOST}${API_CHECK_IN}`, payload);
        if (resp.code !== 200) {
            if (resp.code === 299) {
                console.log(resp.businessCode);
            } else {
                console.error(`签到失败：${resp.businessCode}`);
            }
        }
        return resp;
    }
    
    /**
     * 获取文章列表
     * @returns 
     */
    async get_article_list() {
        const payload = {
            pageNum: 1,
            pageSize: 10,
            boardCode: '0'
        }
        return fetch.post(`${BMW_SERVER_HOST}${API_ARTICLE_LIST}`, payload);
    }

    /**
     * 刷新joy币信息
     * @returns 
     */
    async get_joy_info() {
        const payload = {"copId":null,"eventCode":null};
        return fetch.post(`${BMW_SERVER_HOST}${API_JOY_INFO}`, payload);
    }

    /**
     * 获取joy币信息
     * @returns
     */
    async get_joy_list() {
        return await fetch.post(`${BMW_SERVER_HOST}${API_JOY_LIST}`, {});
    }
    
    /**
     * 分享文章
     * @returns
     */
    async share_article() {
        const article_info = await this.get_article_list();
        const articles = article_info.data.articleVos;
        if (!Array.isArray(articles) || articles.length === 0) {
            console.warn("没有可供分享的文章，跳过分享");
            return;
        }
        const article_id = articles[0].articleId;
        const article_title = articles[0].articleTitle;
        const payload = {
            'articleId': article_id
        };
        const resp = await fetch.post(`${BMW_SERVER_HOST}${API_SHARE_ARTICLE}`, payload);
        if (resp.code === 200 && resp.success === true) {
            await this.get_joy_info();
            console.log(`分享文章 "${article_title}" 成功`);
        }
    }

    /**
     * 执行完整的签到操作
     */
    async do_check_in() {
        let joy_list = await this.get_joy_list();
        const joy_coin_count_before = joy_list.data.joyCoin;

        const resp = await this.check_in();
        const already_signed_in = resp.code === 299;
        if (already_signed_in) {
            return;
        }
        await this.share_article();
        await new Promise(r => setTimeout(r, 1000));

        joy_list = await this.get_joy_list();
        const joy_coin_count_after = joy_list.data.joyCoin;
        const joy_social_header = joy_list.data.joySocialHeader;
        const to_expire_joy_coin = joy_list.data.toExpireJoyCoin;
        console.log(`签到成功，本次签到共获得 ${joy_coin_count_after - joy_coin_count_before} 个Joy币`);
        if (to_expire_joy_coin !== 0) {
            console.log(joy_social_header + "请注意及时使用");
        }
    }
}

async function main() {
    const is_github_action = process.env['GITHUB_ACTIONS'] === 'true';
    if (is_github_action) {
        const access_token = process.env['BMW_ACCESS_TOKEN'];
        const refresh_token = process.env['BMW_REFRESH_TOKEN'];
        if (!access_token || !refresh_token) {
            console.log("not enabled");
            return;
        }
    }

    const client = new myBMWClient();
    await client.load_token(is_github_action);
    await client.do_check_in();
}

try {
    main();
} catch (e) {
    console.error("签到失败", e);
}
