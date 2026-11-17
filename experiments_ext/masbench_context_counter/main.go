// Offline vocabulary and template candidate for the pinned Ollama source.
// No HTTP, tensor context, generation, backend discovery or GPU initialization.
package main

import (
    "bytes"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "os"
    "unicode/utf8"

    "github.com/ollama/ollama/api"
    "github.com/ollama/ollama/llama"
    ot "github.com/ollama/ollama/template"
)

type Message struct { Role string `json:"role"`; Content string `json:"content"` }
type Request struct { Messages []Message `json:"messages"` }
type Input struct {
    ModelPath string `json:"model_path"`
    TemplatePath string `json:"template_path"`
    TemplateSHA string `json:"template_sha256"`
    Requests []Request `json:"requests"`
    Texts []string `json:"texts"`
}
type Row struct {
    Rendered string `json:"rendered"`
    RenderSHA string `json:"rendered_sha256"`
    Bytes int `json:"utf8_bytes"`
    Tokens []int `json:"token_ids"`
    TokenSHA string `json:"token_ids_json_sha256"`
    Count int `json:"token_count"`
}
func hash(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func run() error {
    raw, err := io.ReadAll(io.LimitReader(os.Stdin, 4*1024*1024+1))
    if err != nil { return err }
    if len(raw)>4*1024*1024 || !utf8.Valid(raw) { return errors.New("invalid or oversized UTF-8 input") }
    var in Input
    d := json.NewDecoder(bytes.NewReader(raw)); d.DisallowUnknownFields()
    if err := d.Decode(&in); err != nil { return err }
    var extra any
    if err := d.Decode(&extra); err != io.EOF { return errors.New("trailing JSON") }
    if len(in.Requests)+len(in.Texts)>128 || len(in.Requests)+len(in.Texts)==0 { return errors.New("case cap") }
    tb, err := os.ReadFile(in.TemplatePath); if err != nil { return err }
    if len(in.TemplateSHA)!=64 || hash(tb)!=in.TemplateSHA { return errors.New("template SHA mismatch") }
    t, err := ot.Parse(string(tb)); if err != nil { return err }
    // This is the legacy engine's actual vocabulary loader and flags. No
    // BackendInit or NewContextWithModel: those are outside this helper.
    m, err := llama.LoadModelFromFile(in.ModelPath, llama.ModelParams{VocabOnly:true, NumGpuLayers:0})
    if err != nil { return err }; defer llama.FreeModel(m)
    makeRow := func(s string) (Row,error) {
        ids, e := m.Tokenize(s,false,true); if e != nil { return Row{},e }
        b,e := json.Marshal(ids); if e != nil { return Row{},e }
        return Row{s,hash([]byte(s)),len([]byte(s)),ids,hash(b),len(ids)},nil
    }
    rows := make([]Row,0,len(in.Requests)); texts := make([]Row,0,len(in.Texts))
    for _, r := range in.Requests {
        if len(r.Messages)==0 || len(r.Messages)>64 { return errors.New("message cap") }
        msgs := make([]api.Message,0,len(r.Messages))
        for _, v := range r.Messages {
            if v.Role!="system" && v.Role!="user" && v.Role!="assistant" { return errors.New("unsupported role") }
            msgs=append(msgs,api.Message{Role:v.Role,Content:v.Content})
        }
        var b bytes.Buffer
        if err:=t.Execute(&b,ot.Values{Messages:msgs}); err!=nil { return err }
        row,e:=makeRow(b.String()); if e!=nil { return e }; rows=append(rows,row)
    }
    for _,s:=range in.Texts { row,e:=makeRow(s); if e!=nil { return e }; texts=append(texts,row) }
    return json.NewEncoder(os.Stdout).Encode(map[string]any{
        "status":"offline_candidate_not_deployment_verified", "source_commit":"92b96d54efd6b49322b7cf046f9a0dc16b00cd0a",
        "template_sha256":hash(tb), "input_sha256":hash(raw), "vocab_only":true,
        "add_special":false,"parse_special":true,"tensor_context_created":false,
        "requests":rows,"texts":texts,
    })
}
func main() { if err:=run();err!=nil { fmt.Fprintln(os.Stderr,err);os.Exit(1) } }
